# @pfat/climadiag

Port du composant « Climadiag commune » de
[plusfraichemaville-site](https://github.com/incubateur-ademe/plusfraichemaville-site/tree/36b2669fc9c226215f2833ac73d4e525d3a6a6c3/src/components/climadiag)
(sans Next.js / prisma / tailwind).

```sh
npm install
npm run dev
```

## Données

`src/sample-data.ts` contient des valeurs d'exemple. L'API du site
(`/api/search-climadiag-info`) exige une session (401 en anonyme) — quand on
aura un accès, remplacer ce module par un fetch (mêmes types `Climadiag`).

Non porté (YAGNI pour l'instant) : export PDF (`climadiag-downloader`),
recherche asynchrone (`climadiag-panel`, dépend de leur API).

Les données Climadiag sont la propriété exclusive de Météo-France.
