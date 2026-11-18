import { useEffect } from "react";
import { isRouteErrorResponse, useRouteError } from "react-router";

import { ErrorPage } from "@/features/error/ErrorPage";
import { reportError } from "@/lib/errors";

export function RouteError() {
  const error = useRouteError();
  const knownResponse = isRouteErrorResponse(error);
  useEffect(() => {
    if (!knownResponse) reportError(error);
  }, [error, knownResponse]);

  return <ErrorPage kind={knownResponse && error.status === 404 ? "not-found" : "server"} />;
}
