import { AppShell, Burger, Group, NavLink, Text, Title } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { NavLink as RouterLink, Outlet, useLocation } from "react-router";
import { useInfo } from "@/api/queries";

const LINKS = [
  { to: "/", label: "Catálogo" },
  { to: "/owners", label: "Times" },
  { to: "/templates", label: "Templates" },
  { to: "/environments", label: "Ambientes" },
  { to: "/tasks", label: "Tasks" },
];

function Footer() {
  const info = useInfo();
  if (info.isPending) return <Text size="xs">Carregando versão...</Text>;
  if (info.error)
    return (
      <Text size="xs" c="red">
        API indisponível
      </Text>
    );
  return (
    <Text size="xs" c="dimmed">
      {info.data.product} · API {info.data.api_version} · spec v{info.data.spec_version}
    </Text>
  );
}

export function Layout() {
  const [opened, { toggle, close }] = useDisclosure();
  const { pathname } = useLocation();
  const active = (to: string) =>
    to === "/" ? pathname === "/" || pathname.startsWith("/components") : pathname.startsWith(to);
  return (
    <AppShell
      header={{ height: 56 }}
      footer={{ height: 36 }}
      navbar={{ width: 220, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" aria-label="Menu" />
          <Title order={3}>purr</Title>
          <Text c="dimmed" size="sm">
            Plataforma interna de desenvolvimento
          </Text>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        <nav aria-label="Navegação principal">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              component={RouterLink}
              to={l.to}
              end={l.to === "/"}
              label={l.label}
              active={active(l.to)}
              onClick={close}
            />
          ))}
        </nav>
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
      <AppShell.Footer p="xs">
        <Footer />
      </AppShell.Footer>
    </AppShell>
  );
}
