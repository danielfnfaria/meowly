import { Stack, Table, Title } from "@mantine/core";
import { useEnvironments, useOwners, useTemplates } from "@/api/queries";
import { QueryState } from "@/components/QueryState";

export function Owners() {
  const query = useOwners();
  return (
    <Stack>
      <Title order={2}>Times</Title>
      <QueryState query={query} empty="Nenhum time cadastrado ainda.">
        {(items) => (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Slug</Table.Th>
                <Table.Th>Nome</Table.Th>
                <Table.Th>E-mail</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((o) => (
                <Table.Tr key={o.id}>
                  <Table.Td>{o.slug}</Table.Td>
                  <Table.Td>{o.name}</Table.Td>
                  <Table.Td>{o.email ?? "—"}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </QueryState>
    </Stack>
  );
}

export function Templates() {
  const query = useTemplates();
  return (
    <Stack>
      <Title order={2}>Templates</Title>
      <QueryState query={query} empty="Nenhum template cadastrado ainda.">
        {(items) => (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Slug</Table.Th>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Origem</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((t) => (
                <Table.Tr key={t.id}>
                  <Table.Td>{t.slug}</Table.Td>
                  <Table.Td>{t.name}</Table.Td>
                  <Table.Td>{t.source_url}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </QueryState>
    </Stack>
  );
}

export function Environments() {
  const query = useEnvironments();
  return (
    <Stack>
      <Title order={2}>Ambientes</Title>
      <QueryState query={query} empty="Nenhum ambiente cadastrado ainda.">
        {(items) => (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Slug</Table.Th>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Descrição</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((e) => (
                <Table.Tr key={e.id}>
                  <Table.Td>{e.slug}</Table.Td>
                  <Table.Td>{e.name}</Table.Td>
                  <Table.Td>{e.description ?? "—"}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </QueryState>
    </Stack>
  );
}
