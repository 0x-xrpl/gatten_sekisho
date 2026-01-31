export type SubmitRequest = {
  user_request: string;
  context?: Record<string, unknown>;
};

export type ExecuteRequest = {
  permit_id: string;
  action: Record<string, unknown>;
};

export type ApiResult<T = unknown> = {
  ok: boolean;
  status: number;
  data: T | null;
  errorText?: string;
};

export type GateSubmitResponse = Record<string, unknown>;
export type GateExecuteResponse = Record<string, unknown>;
