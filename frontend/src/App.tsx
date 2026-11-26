import { useEffect, useState } from "react";
import { RouterProvider } from "react-router/dom";

import { AppLoader } from "@/components/layout/AppLoader";
import { Providers } from "@/app/providers";
import { router } from "@/app/router";

export function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // The app is ready once the fonts settle; lazy routes show their own skeletons meanwhile.
    void document.fonts.ready.then(() => setLoading(false));
  }, []);

  return (
    <Providers>
      <AppLoader loading={loading} />
      <RouterProvider router={router} />
    </Providers>
  );
}
