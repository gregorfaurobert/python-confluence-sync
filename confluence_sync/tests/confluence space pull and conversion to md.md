# Sync (pull) confluence space and convert to Mardown

1) Run successfully confluence sync --space OT --pull
2) Expected local Folder structure

```
obsidian-test/
└── Obsidian Test Home/
    ├── FOLDER/
    │   ├── Hello World!/
    │       └── .confluence-sync.json
    │       └── hello-world.md
    ├── Hola/
    │   ├── .confluence-sync.json
    │   └── hola.md
    ├── Test/
    │   ├── .confluence-sync.json
    │   ├── test.md
    │   └── _attachments/
    │       └── Image-1.png
    ├── .confluence-sync.json
    └── obsidian-test-home.md
```

3) HTML Confluence to Markdown conversion
Use as benchmark the page "Test"
The confluence 2 markdown converter must be able to convert test_page.html into test-expected.md


