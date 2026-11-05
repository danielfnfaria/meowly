import { Alert, Center, Loader, Text } from "@mantine/core";
import { ApiError } from "@/api/client";
import type { ReactNode } from "react";

interface Props<T> {
  query: { data: T | undefined; error: Error | null; isPending: boolean };
  /** Shown when the list came back empty. */
  empty: string;
  children: (data: T) => ReactNode;
}

/** Loading, error and empty states shared by every list; `children` renders only real data. */
export function QueryState<T>({ query, empty, children }: Props<T>) {
  if (query.isPending) {
    return (
      <Center py="xl">
        <Loader size="sm" />
      </Center>
    );
  }
  if (query.error) {
    const code = query.error instanceof ApiError ? ` (${query.error.code})` : "";
    return (
      <Alert color="red" title="Não foi possível carregar" role="alert">
        {query.error.message}
        {code}
      </Alert>
    );
  }
  const data = query.data as T;
  if (Array.isArray(data) && data.length === 0) {
    return <Text c="dimmed">{empty}</Text>;
  }
  return <>{children(data)}</>;
}
