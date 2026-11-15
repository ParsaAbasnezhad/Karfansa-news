import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useHealth } from "@/hooks/use-health";
import { getErrorMessage } from "@/lib/errors";

import styles from "./StatusPage.module.css";

/** Minimal starter page proving the frontend can reach the backend. */
export function StatusPage() {
  const { data, error, isPending, isFetching, refetch } = useHealth();

  return (
    <div className={styles.stack}>
      <h1 className={styles.title}>Project foundation</h1>
      <p className={styles.muted}>Backend connectivity check.</p>

      <Card>
        {isPending && <p>Checking backend…</p>}
        {error && <p className={styles.bad}>Backend unreachable: {getErrorMessage(error)}</p>}
        {data && (
          <ul className={styles.list}>
            <li className={styles.row}>
              <span>api</span>
              <span className={data.status === "ok" ? styles.ok : styles.bad}>{data.status}</span>
            </li>
            {Object.entries(data.checks).map(([name, result]) => (
              <li key={name} className={styles.row}>
                <span>{name}</span>
                <span className={result === "ok" ? styles.ok : styles.bad}>{result}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div>
        <Button onClick={() => void refetch()} disabled={isFetching}>
          Re-check
        </Button>
      </div>
    </div>
  );
}
