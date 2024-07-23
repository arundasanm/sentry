export enum SpanMetricsField {
  SPAN_OP = 'span.op',
  SPAN_DESCRIPTION = 'span.description',
  SPAN_MODULE = 'span.module',
  SPAN_ACTION = 'span.action',
  SPAN_DOMAIN = 'span.domain',
  SPAN_GROUP = 'span.group',
  SPAN_DURATION = 'span.duration',
  SPAN_SELF_TIME = 'span.self_time',
  PROJECT = 'project',
  PROJECT_ID = 'project.id',
  TRANSACTION = 'transaction',
  RESOURCE_RENDER_BLOCKING_STATUS = 'resource.render_blocking_status',
  HTTP_RESPONSE_CONTENT_LENGTH = 'http.response_content_length',
  HTTP_DECODED_RESPONSE_CONTENT_LENGTH = 'http.decoded_response_content_length',
  HTTP_RESPONSE_TRANSFER_SIZE = 'http.response_transfer_size',
  FILE_EXTENSION = 'file_extension',
  AI_TOTAL_TOKENS_USED = 'ai.total_tokens.used',
  AI_TOTAL_COST = 'ai.total_cost',
  OS_NAME = 'os.name',
  APP_START_TYPE = 'app_start_type',
  DEVICE_CLASS = 'device.class',
  CACHE_HIT = 'cache.hit',
  CACHE_ITEM_SIZE = 'cache.item_size',
  MESSAGING_MESSAGE_RECEIVE_LATENCY = 'messaging.message.receive.latency',
}

export enum SpanIndexedField {
  ENVIRONMENT = 'environment',
  RESOURCE_RENDER_BLOCKING_STATUS = 'resource.render_blocking_status',
  HTTP_RESPONSE_CONTENT_LENGTH = 'http.response_content_length',
  SPAN_CATEGORY = 'span.category',
  SPAN_DURATION = 'span.duration',
  SPAN_SELF_TIME = 'span.self_time',
  SPAN_GROUP = 'span.group', // Span group computed from the normalized description. Matches the group in the metrics data set
  SPAN_MODULE = 'span.module',
  SPAN_DESCRIPTION = 'span.description',
  SPAN_STATUS = 'span.status',
  SPAN_OP = 'span.op',
  ID = 'span_id',
  SPAN_ACTION = 'span.action',
  SPAN_AI_PIPELINE_GROUP = 'span.ai.pipeline.group',
  SDK_NAME = 'sdk.name',
  TRACE = 'trace',
  TRANSACTION_ID = 'transaction.id',
  TRANSACTION_METHOD = 'transaction.method',
  TRANSACTION_OP = 'transaction.op',
  SPAN_DOMAIN = 'span.domain',
  TIMESTAMP = 'timestamp',
  RAW_DOMAIN = 'raw_domain',
  PROJECT = 'project',
  PROJECT_ID = 'project_id',
  PROFILE_ID = 'profile_id',
  RELEASE = 'release',
  TRANSACTION = 'transaction',
  ORIGIN_TRANSACTION = 'origin.transaction',
  REPLAY_ID = 'replay.id',
  BROWSER_NAME = 'browser.name',
  USER = 'user',
  USER_ID = 'user.id',
  USER_EMAIL = 'user.email',
  USER_USERNAME = 'user.username',
  INP = 'measurements.inp',
  INP_SCORE = 'measurements.score.inp',
  INP_SCORE_WEIGHT = 'measurements.score.weight.inp',
  TOTAL_SCORE = 'measurements.score.total',
  RESPONSE_CODE = 'span.status_code',
  CACHE_HIT = 'cache.hit',
  CACHE_ITEM_SIZE = 'measurements.cache.item_size',
  TRACE_STATUS = 'trace.status',
  MESSAGING_MESSAGE_ID = 'messaging.message.id',
  MESSAGING_MESSAGE_BODY_SIZE = 'measurements.messaging.message.body.size',
  MESSAGING_MESSAGE_RECEIVE_LATENCY = 'measurements.messaging.message.receive.latency',
  MESSAGING_MESSAGE_RETRY_COUNT = 'measurements.messaging.message.retry.count',
  MESSAGING_MESSAGE_DESTINATION_NAME = 'messaging.destination.name',
}