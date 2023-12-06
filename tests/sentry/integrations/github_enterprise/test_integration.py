from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

import responses
from isodate import parse_datetime

from sentry.integrations.github_enterprise import GitHubEnterpriseIntegrationProvider
from sentry.models.identity import Identity, IdentityProvider, IdentityStatus
from sentry.models.integrations.integration import Integration
from sentry.models.integrations.organization_integration import OrganizationIntegration
from sentry.models.repository import Repository
from sentry.silo.base import SiloMode
from sentry.testutils.cases import IntegrationTestCase
from sentry.testutils.silo import assume_test_silo_mode, control_silo_test


@control_silo_test
class GitHubEnterpriseIntegrationTest(IntegrationTestCase):
    provider = GitHubEnterpriseIntegrationProvider
    config = {
        "url": "https://github.example.org",
        "id": 2,
        "name": "test-app",
        "client_id": "client_id",
        "client_secret": "client_secret",
        "webhook_secret": "webhook_secret",
        "private_key": "private_key",
        "verify_ssl": True,
    }
    base_url = "https://github.example.org/api/v3"

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github.client.get_jwt", return_value="jwt_token_1")
    def assert_setup_flow(
        self, get_jwt, _, installation_id="install_id_1", app_id="app_1", user_id="user_id_1"
    ):
        responses.reset()
        resp = self.client.get(self.init_path)
        assert resp.status_code == 200
        resp = self.client.post(self.init_path, data=self.config)
        assert resp.status_code == 302
        redirect = urlparse(resp["Location"])
        assert redirect.scheme == "https"
        assert redirect.netloc == "github.example.org"
        assert redirect.path == "/github-apps/test-app"

        # App installation ID is provided, mveo thr
        resp = self.client.get(
            "{}?{}".format(self.setup_path, urlencode({"installation_id": installation_id}))
        )

        assert resp.status_code == 302
        redirect = urlparse(resp["Location"])
        assert redirect.scheme == "https"
        assert redirect.netloc == "github.example.org"
        assert redirect.path == "/login/oauth/authorize"

        params = parse_qs(redirect.query)
        assert params["state"]
        assert params["redirect_uri"] == ["http://testserver/extensions/github-enterprise/setup/"]
        assert params["response_type"] == ["code"]
        assert params["client_id"] == ["client_id"]
        # once we've asserted on it, switch to a singular values to make life
        # easier
        authorize_params = {k: v[0] for k, v in params.items()}

        access_token = "xxxxx-xxxxxxxxx-xxxxxxxxxx-xxxxxxxxxxxx"

        responses.add(
            responses.POST,
            "https://github.example.org/login/oauth/access_token",
            json={"access_token": access_token},
        )

        responses.add(
            responses.POST,
            self.base_url + f"/app/installations/{installation_id}/access_tokens",
            json={"token": access_token, "expires_at": "3000-01-01T00:00:00Z"},
        )

        responses.add(responses.GET, self.base_url + "/user", json={"id": user_id})

        responses.add(
            responses.GET,
            self.base_url + f"/app/installations/{installation_id}",
            json={
                "id": installation_id,
                "app_id": app_id,
                "account": {
                    "login": "Test Organization",
                    "type": "Organization",
                    "avatar_url": "https://github.example.org/avatar.png",
                    "html_url": "https://github.example.org/Test-Organization",
                },
            },
        )

        responses.add(
            responses.GET,
            self.base_url + "/user/installations",
            json={"installations": [{"id": installation_id}]},
        )

        resp = self.client.get(
            "{}?{}".format(
                self.setup_path,
                urlencode({"code": "oauth-code", "state": authorize_params["state"]}),
            )
        )

        mock_access_token_request = responses.calls[0].request
        req_params = parse_qs(mock_access_token_request.body)
        assert req_params["grant_type"] == ["authorization_code"]
        assert req_params["code"] == ["oauth-code"]
        assert req_params["redirect_uri"] == [
            "http://testserver/extensions/github-enterprise/setup/"
        ]
        assert req_params["client_id"] == ["client_id"]
        assert req_params["client_secret"] == ["client_secret"]

        assert resp.status_code == 200

        auth_header = responses.calls[2].request.headers["Authorization"]
        assert auth_header == "Bearer jwt_token_1"

        self.assertDialogSuccess(resp)

    @responses.activate
    def test_basic_flow(self):
        self.assert_setup_flow()

        integration = Integration.objects.get(provider=self.provider.key)

        assert integration.external_id == "github.example.org:install_id_1"
        assert integration.name == "Test Organization"
        assert integration.metadata == {
            "access_token": None,
            "expires_at": None,
            "icon": "https://github.example.org/avatar.png",
            "domain_name": "github.example.org/Test-Organization",
            "account_type": "Organization",
            "installation_id": "install_id_1",
            "installation": {
                "client_id": "client_id",
                "client_secret": "client_secret",
                "id": "2",
                "name": "test-app",
                "private_key": "private_key",
                "url": "github.example.org",
                "webhook_secret": "webhook_secret",
                "verify_ssl": True,
            },
        }
        oi = OrganizationIntegration.objects.get(
            integration=integration, organization_id=self.organization.id
        )
        assert oi.config == {}

        idp = IdentityProvider.objects.get(type="github_enterprise")
        identity = Identity.objects.get(idp=idp, user=self.user, external_id="user_id_1")
        assert identity.status == IdentityStatus.VALID
        assert identity.data == {"access_token": "xxxxx-xxxxxxxxx-xxxxxxxxxx-xxxxxxxxxxxx"}

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_repositories_search_param(self, mock_jwtm, _):
        with self.tasks():
            self.assert_setup_flow()

        querystring = urlencode({"q": "org:Test Organization ex"})
        responses.add(
            responses.GET,
            f"{self.base_url}/search/repositories?{querystring}",
            json={
                "items": [
                    {"name": "example", "full_name": "test/example", "default_branch": "main"},
                    {"name": "exhaust", "full_name": "test/exhaust", "default_branch": "main"},
                ]
            },
        )
        integration = Integration.objects.get(provider=self.provider.key)
        installation = integration.get_installation(self.organization.id)
        result = installation.get_repositories("ex")
        assert result == [
            {"identifier": "test/example", "name": "example", "default_branch": "main"},
            {"identifier": "test/exhaust", "name": "exhaust", "default_branch": "main"},
        ]

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_stacktrace_link_file_exists(self, get_jwt, _):
        self.assert_setup_flow()
        integration = Integration.objects.get(provider=self.provider.key)

        with assume_test_silo_mode(SiloMode.REGION):
            repo = Repository.objects.create(
                organization_id=self.organization.id,
                name="Test-Organization/foo",
                url="https://github.example.org/Test-Organization/foo",
                provider="integrations:github_enterprise",
                external_id=123,
                config={"name": "Test-Organization/foo"},
                integration_id=integration.id,
            )

        path = "README.md"
        version = "1234567"
        default = "master"
        responses.add(
            responses.HEAD,
            self.base_url + f"/repos/{repo.name}/contents/{path}?ref={version}",
        )
        installation = integration.get_installation(self.organization.id)
        result = installation.get_stacktrace_link(repo, path, default, version)

        assert result == "https://github.example.org/Test-Organization/foo/blob/1234567/README.md"

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_stacktrace_link_file_doesnt_exists(self, get_jwt, _):
        self.assert_setup_flow()
        integration = Integration.objects.get(provider=self.provider.key)

        with assume_test_silo_mode(SiloMode.REGION):
            repo = Repository.objects.create(
                organization_id=self.organization.id,
                name="Test-Organization/foo",
                url="https://github.example.org/Test-Organization/foo",
                provider="integrations:github_enterprise",
                external_id=123,
                config={"name": "Test-Organization/foo"},
                integration_id=integration.id,
            )
        path = "README.md"
        version = "master"
        default = "master"
        responses.add(
            responses.HEAD,
            self.base_url + f"/repos/{repo.name}/contents/{path}?ref={version}",
            status=404,
        )
        installation = integration.get_installation(self.organization.id)
        result = installation.get_stacktrace_link(repo, path, default, version)

        assert not result

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_stacktrace_link_no_org_integration(self, get_jwt, _):
        self.assert_setup_flow()
        integration = Integration.objects.get(provider=self.provider.key)

        with assume_test_silo_mode(SiloMode.REGION):
            repo = Repository.objects.create(
                organization_id=self.organization.id,
                name="Test-Organization/foo",
                url="https://github.example.org/Test-Organization/foo",
                provider="integrations:github_enterprise",
                external_id=123,
                config={"name": "Test-Organization/foo"},
                integration_id=integration.id,
            )
        path = "README.md"
        version = "master"
        default = "master"
        responses.add(
            responses.HEAD,
            self.base_url + f"/repos/{repo.name}/contents/{path}?ref={version}",
            status=404,
        )
        OrganizationIntegration.objects.get(
            integration=integration, organization_id=self.organization.id
        ).delete()
        installation = integration.get_installation(self.organization.id)
        result = installation.get_stacktrace_link(repo, path, default, version)

        assert not result

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_stacktrace_link_use_default_if_version_404(self, get_jwt, _):
        self.assert_setup_flow()
        integration = Integration.objects.get(provider=self.provider.key)

        with assume_test_silo_mode(SiloMode.REGION):
            repo = Repository.objects.create(
                organization_id=self.organization.id,
                name="Test-Organization/foo",
                url="https://github.example.org/Test-Organization/foo",
                provider="integrations:github_enterprise",
                external_id=123,
                config={"name": "Test-Organization/foo"},
                integration_id=integration.id,
            )
        path = "README.md"
        version = "12345678"
        default = "master"
        responses.add(
            responses.HEAD,
            self.base_url + f"/repos/{repo.name}/contents/{path}?ref={version}",
            status=404,
        )
        responses.add(
            responses.HEAD,
            self.base_url + f"/repos/{repo.name}/contents/{path}?ref={default}",
        )
        installation = integration.get_installation(self.organization.id)
        result = installation.get_stacktrace_link(repo, path, default, version)

        assert result == "https://github.example.org/Test-Organization/foo/blob/master/README.md"

    @patch("sentry.integrations.github_enterprise.integration.get_jwt", return_value="jwt_token_1")
    @patch("sentry.integrations.github_enterprise.client.get_jwt", return_value="jwt_token_1")
    @responses.activate
    def test_get_commit_context(self, get_jwt, _):
        self.assert_setup_flow()
        integration = Integration.objects.get(provider=self.provider.key)
        with assume_test_silo_mode(SiloMode.REGION):
            repo = Repository.objects.create(
                organization_id=self.organization.id,
                name="Test-Organization/foo",
                url="https://github.example.org/Test-Organization/foo",
                provider="integrations:github_enterprise",
                external_id=123,
                config={"name": "Test-Organization/foo"},
                integration_id=integration.id,
            )

        installation = integration.get_installation(self.organization.id)

        filepath = "sentry/tasks.py"
        event_frame = {
            "function": "handle_set_commits",
            "abs_path": "/usr/src/sentry/src/sentry/tasks.py",
            "module": "sentry.tasks",
            "in_app": True,
            "lineno": 30,
            "filename": "sentry/tasks.py",
        }
        ref = "master"
        query = f"""query {{
            repository(name: "foo", owner: "Test-Organization") {{
                ref(qualifiedName: "{ref}") {{
                    target {{
                        ... on Commit {{
                            blame(path: "{filepath}") {{
                                ranges {{
                                        commit {{
                                            oid
                                            author {{
                                                name
                                                email
                                            }}
                                            message
                                            committedDate
                                        }}
                                    startingLine
                                    endingLine
                                    age
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}"""
        commit_date = (datetime.now(tz=timezone.utc) - timedelta(days=4)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        responses.add(
            method=responses.POST,
            url="https://github.example.org/api/graphql",
            json={
                "query": query,
                "data": {
                    "repository": {
                        "ref": {
                            "target": {
                                "blame": {
                                    "ranges": [
                                        {
                                            "commit": {
                                                "oid": "d42409d56517157c48bf3bd97d3f75974dde19fb",
                                                "author": {
                                                    "date": commit_date,
                                                    "email": "nisanthan.nanthakumar@sentry.io",
                                                    "name": "Nisanthan Nanthakumar",
                                                },
                                                "message": "Add installation instructions",
                                                "committedDate": commit_date,
                                            },
                                            "startingLine": 30,
                                            "endingLine": 30,
                                            "age": 3,
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
            },
            content_type="application/json",
        )
        commit_context = installation.get_commit_context(repo, filepath, ref, event_frame)

        commit_context_expected = {
            "commitId": "d42409d56517157c48bf3bd97d3f75974dde19fb",
            "committedDate": parse_datetime(commit_date),
            "commitMessage": "Add installation instructions",
            "commitAuthorName": "Nisanthan Nanthakumar",
            "commitAuthorEmail": "nisanthan.nanthakumar@sentry.io",
        }

        assert commit_context == commit_context_expected
