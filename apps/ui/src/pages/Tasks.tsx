import { Alert, Anchor, Button, Card, Select, Stack, Table, Text, Title } from "@mantine/core";
import { useState, type SyntheticEvent } from "react";
import { Link } from "react-router";
import { useComponents, useCreateTask, useTask, useTasks } from "@/api/queries";
import { PhaseBadge } from "@/components/PhaseBadge";
import { QueryState } from "@/components/QueryState";
import type { TaskKind } from "@/api/client";

const KINDS: TaskKind[] = ["noop", "scaffold", "provision"];

function NewTaskForm() {
  const components = useComponents();
  const create = useCreateTask();
  const [component, setComponent] = useState<string | null>(null);
  const [kind, setKind] = useState<string | null>("noop");

  const submit = (e: SyntheticEvent) => {
    e.preventDefault();
    if (!component || !kind) return;
    create.mutate({ kind: kind as TaskKind, component });
  };

  return (
    <Card component="form" onSubmit={submit} aria-label="Nova task">
      <Stack gap="xs">
        <Title order={4}>Nova task</Title>
        <Select
          label="Componente"
          required
          placeholder={components.data?.length === 0 ? "Nenhum componente cadastrado" : "Selecione"}
          data={(components.data ?? []).map((c) => ({ value: c.slug, label: c.name }))}
          value={component}
          onChange={setComponent}
        />
        <Select
          label="Tipo"
          required
          allowDeselect={false}
          data={KINDS}
          value={kind}
          onChange={setKind}
        />
        {create.error && (
          <Alert color="red" role="alert">
            {create.error.message}
          </Alert>
        )}
        <Button type="submit" loading={create.isPending} disabled={!component || !kind}>
          Criar task
        </Button>
      </Stack>
    </Card>
  );
}

export function Tasks() {
  const tasks = useTasks();
  return (
    <Stack>
      <Title order={2}>Tasks</Title>
      <Alert color="blue">
        Sem cluster (<code>PURR_LAUNCHER=memory</code>, como no <code>make up</code>), a task fica{" "}
        <code>pending</code> e nada a executa.
      </Alert>
      <QueryState query={tasks} empty="Nenhuma task ainda.">
        {(items) => (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Tipo</Table.Th>
                <Table.Th>Fase</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((t) => (
                <Table.Tr key={t.name}>
                  <Table.Td>
                    <Anchor component={Link} to={`/tasks/${t.name}`}>
                      {t.name}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>{t.kind}</Table.Td>
                  <Table.Td>
                    <PhaseBadge phase={t.phase} />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </QueryState>
      <NewTaskForm />
    </Stack>
  );
}

const when = (iso: string | null) => (iso ? new Date(iso).toLocaleString("pt-BR") : "—");

export function TaskDetail({ name }: { name: string }) {
  const task = useTask(name);
  return (
    <Stack>
      <Anchor component={Link} to="/tasks">
        ← Tasks
      </Anchor>
      <QueryState query={task} empty="Task não encontrada.">
        {(t) => (
          <Card>
            <Stack gap="xs">
              <Title order={2}>{t.name}</Title>
              <Text>
                Fase: <PhaseBadge phase={t.phase} />
              </Text>
              <Text>Tipo: {t.kind}</Text>
              <Text>Componente: {t.component ?? "—"}</Text>
              <Text>Mensagem: {t.message ?? "—"}</Text>
              {t.error && <Alert color="red">{t.error}</Alert>}
              <Text>Início: {when(t.started_at)}</Text>
              <Text>Fim: {when(t.finished_at)}</Text>
              <Title order={5}>Outputs</Title>
              {Object.keys(t.outputs).length === 0 ? (
                <Text c="dimmed">Sem outputs.</Text>
              ) : (
                <Table>
                  <Table.Tbody>
                    {Object.entries(t.outputs).map(([k, v]) => (
                      <Table.Tr key={k}>
                        <Table.Td>{k}</Table.Td>
                        <Table.Td>{v}</Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              )}
            </Stack>
          </Card>
        )}
      </QueryState>
    </Stack>
  );
}
