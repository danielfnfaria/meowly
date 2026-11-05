import { Anchor, Button, Card, Select, Stack, Table, TextInput, Title } from "@mantine/core";
import { useState, type SyntheticEvent } from "react";
import { Link } from "react-router";
import { useComponents, useCreateComponent, useOwners } from "@/api/queries";
import { QueryState } from "@/components/QueryState";

function CreateComponentForm() {
  const owners = useOwners();
  const create = useCreateComponent();
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [system, setSystem] = useState("");
  const [ownerId, setOwnerId] = useState<string | null>(null);

  const submit = (e: SyntheticEvent) => {
    e.preventDefault();
    if (!ownerId) return;
    create.mutate(
      { slug, name, owner_id: ownerId, system: system || null },
      {
        onSuccess: () => {
          setSlug("");
          setName("");
          setSystem("");
        },
      },
    );
  };

  return (
    <Card component="form" onSubmit={submit} aria-label="Novo componente">
      <Stack gap="xs">
        <Title order={4}>Novo componente</Title>
        <TextInput
          label="Slug"
          required
          value={slug}
          onChange={(e) => {
            setSlug(e.currentTarget.value);
          }}
        />
        <TextInput
          label="Nome"
          required
          value={name}
          onChange={(e) => {
            setName(e.currentTarget.value);
          }}
        />
        <TextInput
          label="Sistema"
          value={system}
          onChange={(e) => {
            setSystem(e.currentTarget.value);
          }}
        />
        <Select
          label="Time"
          required
          placeholder={owners.data?.length === 0 ? "Nenhum time cadastrado" : "Selecione"}
          data={(owners.data ?? []).map((o) => ({ value: o.id, label: o.name }))}
          value={ownerId}
          onChange={setOwnerId}
        />
        {create.error && (
          <span role="alert" style={{ color: "var(--mantine-color-red-6)" }}>
            {create.error.message}
          </span>
        )}
        <Button type="submit" loading={create.isPending} disabled={!ownerId}>
          Criar componente
        </Button>
      </Stack>
    </Card>
  );
}

export function Catalog() {
  const components = useComponents();
  const owners = useOwners();
  const ownerName = new Map((owners.data ?? []).map((o) => [o.id, o.name]));
  return (
    <Stack>
      <Title order={2}>Catálogo</Title>
      <QueryState query={components} empty="Nenhum componente cadastrado ainda.">
        {(items) => (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Slug</Table.Th>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Time</Table.Th>
                <Table.Th>Sistema</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((c) => (
                <Table.Tr key={c.id}>
                  <Table.Td>
                    <Anchor component={Link} to={`/components/${c.slug}`}>
                      {c.slug}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>{c.name}</Table.Td>
                  <Table.Td>{ownerName.get(c.owner_id) ?? c.owner_id}</Table.Td>
                  <Table.Td>{c.system ?? "—"}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </QueryState>
      <CreateComponentForm />
    </Stack>
  );
}
