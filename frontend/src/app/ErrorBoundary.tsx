import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
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
    return (
      <div role="alert" style={{ padding: "2rem" }}>
        <h1>Something went wrong</h1>
        <p>Please reload the page and try again.</p>
        <Button onClick={() => window.location.reload()}>Reload</Button>
      </div>
    );
  }
}
