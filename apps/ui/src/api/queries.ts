import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, unwrap, type ComponentCreate, type TaskCreate } from "./client";

export const useInfo = () =>
  useQuery({ queryKey: ["info"], queryFn: async () => unwrap(await api.GET("/v1/info")) });

export const useOwners = () =>
  useQuery({ queryKey: ["owners"], queryFn: async () => unwrap(await api.GET("/v1/owners")) });

export const useComponents = () =>
  useQuery({
    queryKey: ["components"],
    queryFn: async () => unwrap(await api.GET("/v1/components")),
  });

export const useComponent = (slug: string) =>
  useQuery({
    queryKey: ["components", slug],
    queryFn: async () =>
      unwrap(await api.GET("/v1/components/{slug}", { params: { path: { slug } } })),
  });

export const useTemplates = () =>
  useQuery({
    queryKey: ["templates"],
    queryFn: async () => unwrap(await api.GET("/v1/templates")),
  });

export const useEnvironments = () =>
  useQuery({
    queryKey: ["environments"],
    queryFn: async () => unwrap(await api.GET("/v1/environments")),
  });

export const useTasks = () =>
  useQuery({ queryKey: ["tasks"], queryFn: async () => unwrap(await api.GET("/v1/tasks")) });

export const useTask = (name: string) =>
  useQuery({
    queryKey: ["tasks", name],
    queryFn: async () => unwrap(await api.GET("/v1/tasks/{name}", { params: { path: { name } } })),
  });

export function useCreateComponent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ComponentCreate) => unwrap(await api.POST("/v1/components", { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["components"] }),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TaskCreate) => unwrap(await api.POST("/v1/tasks", { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}
