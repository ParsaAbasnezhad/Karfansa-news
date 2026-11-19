import styles from "./InstallAppButton.module.css";

type InstallAppButtonProps = {
  placement?: "header" | "drawer";
};

export function InstallAppButton({ placement = "header" }: InstallAppButtonProps) {
  return (
    <button
      type="button"
      dir="rtl"
      aria-disabled="true"
      className={`${styles.button} ${styles[placement]}`}
    >
      <span className={styles.mark} aria-hidden="true">
        <img src="/KARFANSA%20%E2%80%94%20Logo.svg" alt="" />
      </span>
      <span className={styles.label}>نصب اپلیکیشن</span>
      <span className={styles.status}>به‌زودی</span>
    </button>
  );
}
