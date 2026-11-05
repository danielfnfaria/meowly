import { Anchor, Card, Stack, Text, Title } from "@mantine/core";
import { Link, useParams } from "react-router";
import { useComponent, useOwners } from "@/api/queries";
import { QueryState } from "@/components/QueryState";

export function ComponentDetail() {
  const { slug = "" } = useParams();
  const component = useComponent(slug);
  const owners = useOwners();
  return (
    <Stack>
      <Anchor component={Link} to="/">
        ← Catálogo
      </Anchor>
      <QueryState query={component} empty="Componente não encontrado.">
        {(c) => (
          <Card>
            <Stack gap="xs">
              <Title order={2}>{c.name}</Title>
              <Text>Slug: {c.slug}</Text>
              <Text>Time: {owners.data?.find((o) => o.id === c.owner_id)?.name ?? c.owner_id}</Text>
              <Text>Sistema: {c.system ?? "—"}</Text>
              <Text>Descrição: {c.description ?? "—"}</Text>
              <Text>Repositório: {c.repo_url ?? "—"}</Text>
              <Text c="dimmed" size="sm">
                Criado em {new Date(c.created_at).toLocaleString("pt-BR")}
              </Text>
            </Stack>
          </Card>
        )}
      </QueryState>
    </Stack>
  );
}
