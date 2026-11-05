# apps/ui — a interface administrativa

React 19 + TypeScript (Vite 7), Mantine 8 e TanStack Query. Fica **fora do workspace `uv`**
(ruff e pyright a ignoram) e é buildada dentro do `apps/api/Dockerfile`: em produção a própria
API serve estes assets na mesma origem, com a API sob `/v1` (ADR 0004). Em desenvolvimento o
`make ui` sobe o Vite em `:5173` e o proxy dele manda `/v1` para a API do `make up`.

```
src/
├── api/
│   ├── schema.d.ts    # GERADO do OpenAPI da API — nunca editar à mão
│   ├── client.ts      # o cliente openapi-fetch tipado + ApiError/unwrap
│   └── queries.ts     # os hooks do TanStack Query (uma chave por recurso)
├── components/        # Layout (AppShell + navegação + rodapé com /v1/info), QueryState, PhaseBadge
├── pages/             # Catalog, ComponentDetail, Lists (times/templates/ambientes), Tasks, TaskDetailPage
├── App.tsx            # as rotas
└── __tests__/         # vitest + @testing-library/react (happy-dom)
```

## A regra que não pode ser quebrada

**A UI só fala com a API pelo cliente gerado do OpenAPI.** Nada de `fetch` solto nem de URL
montada à mão numa página: tudo passa por `src/api/client.ts`.

Toda mudança de API que afete a UI **regenera o cliente no mesmo PR**:

```bash
cd apps/ui && npm run generate-api:local     # roda a API deste checkout e regera schema.d.ts
```

`make check-openapi` compara o `schema.d.ts` commitado com o OpenAPI do checkout e falha se
estiverem fora de sincronia — é esse check que transforma uma mudança incompatível de API num
erro de CI, e não num 422 no browser.

## Convenções

- **Textos de interface em pt-BR**; código, nomes de componente e comentários em inglês.
- Toda lista trata os três estados (carregando, erro, vazio) — é para isso que existe
  `QueryState`; uma tela que ignora o erro mente para quem a usa.
- O erro da API é `{code, message}` (declarado como `ErrorOut` no OpenAPI); `toApiError` ainda
  aceita o `{detail}` do FastAPI por defesa.
- Nada de asset binário no repositório: ícone é SVG.
- Node >= 20.19 (o `.nvmrc` fixa 22, que é o que o CI e a imagem usam).

## Comandos

```bash
npm run dev          # Vite direto (prefira `make ui` na raiz: ele confere se a API está no ar)
npm run lint         # eslint (--max-warnings 0)
npm run typecheck    # tsc -b
npm test             # vitest
npm run build        # tsc -b && vite build (é o que roda dentro da imagem da API)
```

Na raiz, `make check-ui` roda lint + typecheck + testes + prettier de uma vez.

## O que esta UI ainda não tem

Autenticação (não há login: a API é aberta e toda task sai como `requested_by: anonymous`),
paginação, filtros, acompanhamento ao vivo de uma task (hoje é refetch do TanStack Query, não
stream) e edição de template/ambiente.
