import {QueryClientProvider} from '@tanstack/react-query';
import {OrganizationFixture} from 'sentry-fixture/organization';

import {makeTestQueryClient} from 'sentry-test/queryClient';
import {renderHook, waitFor} from 'sentry-test/reactTestingLibrary';

import * as useOrganization from 'sentry/utils/useOrganization';

import {useTraceMeta} from './useTraceMeta';

const organization = OrganizationFixture();
const queryClient = makeTestQueryClient();

describe('useTraceMeta', () => {
  beforeEach(function () {
    queryClient.clear();
    jest.clearAllMocks();
    jest.spyOn(useOrganization, 'default').mockReturnValue(organization);
  });

  it('Returns merged metaResults', async () => {
    const traceSlugs = ['slug1', 'slug2', 'slug3'];

    // Mock the API calls
    MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug1/',
      body: {
        errors: 1,
        performance_issues: 1,
        projects: 1,
        transactions: 1,
      },
    });
    MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug2/',
      body: {
        errors: 1,
        performance_issues: 1,
        projects: 1,
        transactions: 1,
      },
    });
    MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug3/',
      body: {
        errors: 1,
        performance_issues: 1,
        projects: 1,
        transactions: 1,
      },
    });

    const wrapper = ({children}: {children: React.ReactNode}) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const {result} = renderHook(() => useTraceMeta(traceSlugs), {wrapper});

    expect(result.current).toEqual({
      data: undefined,
      errors: [],
      isLoading: true,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current).toEqual({
      data: {
        errors: 3,
        performance_issues: 3,
        projects: 1,
        transactions: 3,
      },
      errors: [],
      isLoading: false,
    });
  });

  it('Collects errors from rejected api calls', async () => {
    const traceSlugs = ['slug1', 'slug2', 'slug3'];

    // Mock the API calls
    const mockRequest1 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug1/',
      statusCode: 400,
    });
    const mockRequest2 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug2/',
      statusCode: 400,
    });
    const mockRequest3 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug3/',
      statusCode: 400,
    });

    const wrapper = ({children}: {children: React.ReactNode}) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const {result} = renderHook(() => useTraceMeta(traceSlugs), {wrapper});

    expect(result.current).toEqual({
      data: undefined,
      errors: [],
      isLoading: true,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current).toEqual({
      data: {
        errors: 0,
        performance_issues: 0,
        projects: 0,
        transactions: 0,
      },
      errors: [expect.any(Error), expect.any(Error), expect.any(Error)],
      isLoading: false,
    });

    expect(mockRequest1).toHaveBeenCalledTimes(1);
    expect(mockRequest2).toHaveBeenCalledTimes(1);
    expect(mockRequest3).toHaveBeenCalledTimes(1);
  });

  it('Accumulates metaResults and collects errors from rejected api calls', async () => {
    const traceSlugs = ['slug1', 'slug2', 'slug3'];

    // Mock the API calls
    const mockRequest1 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug1/',
      statusCode: 400,
    });
    const mockRequest2 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug2/',
      body: {
        errors: 1,
        performance_issues: 1,
        projects: 1,
        transactions: 1,
      },
    });
    const mockRequest3 = MockApiClient.addMockResponse({
      method: 'GET',
      url: '/organizations/org-slug/events-trace-meta/slug3/',
      body: {
        errors: 1,
        performance_issues: 1,
        projects: 1,
        transactions: 1,
      },
    });

    const wrapper = ({children}: {children: React.ReactNode}) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const {result} = renderHook(() => useTraceMeta(traceSlugs), {wrapper});

    expect(result.current).toEqual({
      data: undefined,
      errors: [],
      isLoading: true,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current).toEqual({
      data: {
        errors: 2,
        performance_issues: 2,
        projects: 1,
        transactions: 2,
      },
      errors: [expect.any(Error)],
      isLoading: false,
    });

    expect(mockRequest1).toHaveBeenCalledTimes(1);
    expect(mockRequest2).toHaveBeenCalledTimes(1);
    expect(mockRequest3).toHaveBeenCalledTimes(1);
  });
});
