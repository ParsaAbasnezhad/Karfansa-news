import { Component, type ErrorInfo, type ReactNode } from "react";

import { ErrorPage } from "@/features/error/ErrorPage";
import { reportError } from "@/lib/errors";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  override state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    reportError({ error, componentStack: info.componentStack });
  }

  override render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    return <ErrorPage kind="server" />;
  }
}
