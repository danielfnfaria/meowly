import { Route, Routes } from "react-router";
import { Layout } from "@/components/Layout";
import { Catalog } from "@/pages/Catalog";
import { ComponentDetail } from "@/pages/ComponentDetail";
import { Environments, Owners, Templates } from "@/pages/Lists";
import { TaskDetailPage } from "@/pages/TaskDetailPage";
import { Tasks } from "@/pages/Tasks";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Catalog />} />
        <Route path="components/:slug" element={<ComponentDetail />} />
        <Route path="owners" element={<Owners />} />
        <Route path="templates" element={<Templates />} />
        <Route path="environments" element={<Environments />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="tasks/:name" element={<TaskDetailPage />} />
        <Route path="*" element={<Catalog />} />
      </Route>
    </Routes>
  );
}
