import { isRouteErrorResponse, useRouteError } from "react-router";

import { reportError } from "@/lib/errors";

export function RouteError() {
  const error = useRouteError();
  if (!isRouteErrorResponse(error)) reportError(error);

  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : "Unexpected error";

  return (
    <div role="alert" style={{ padding: "2rem" }}>
      <h1>{message}</h1>
    </div>
  );
}
