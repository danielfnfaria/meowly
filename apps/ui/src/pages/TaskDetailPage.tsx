import { useParams } from "react-router";
import { TaskDetail } from "./Tasks";

export function TaskDetailPage() {
  const { name = "" } = useParams();
  return <TaskDetail name={name} />;
}
