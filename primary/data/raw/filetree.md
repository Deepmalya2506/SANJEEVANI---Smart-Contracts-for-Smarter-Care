# File Tree: SANJEEVANi

**Generated:** 9/4/2026, 5:43:13 PM
**Root Path:** `c:\Users\DEEPMALYA\OneDrive\Desktop\pip_Malya\PRODUCTS\SANJEEVANi`

```
├── 📁 GIS_engine
│   ├── 📁 routes
│   │   ├── 🐍 matrix.py
│   │   ├── 🐍 nearest.py
│   │   ├── 🐍 routes.py
│   │   └── 🐍 tiles.py
│   ├── 📁 schemas
│   │   └── 🐍 schema.py
│   ├── 📁 services
│   │   ├── 🐍 geo_service.py
│   │   ├── 🐍 isochrone_service.py
│   │   ├── 🐍 osrm_service.py
│   │   └── 🐍 visualization_service.py
│   ├── 📁 utils
│   │   ├── 🐍 haversine.py
│   │   └── 🐍 helpers.py
│   ├── 🐍 config.py
│   ├── 🌐 isochrone_map.html
│   ├── 🐍 main.py
│   └── 🌐 route_map.html
├── 📁 app
│   ├── 📁 core
│   │   ├── 🐍 config.py
│   │   └── 🐍 database.py
│   ├── 📁 models
│   │   ├── 🐍 hospital.py
│   │   └── 🐍 inventory.py
│   ├── 📁 routes
│   │   ├── 🐍 blockchain.py
│   │   ├── 🐍 dispatch.py
│   │   ├── 🐍 events.py
│   │   ├── 🐍 gis.py
│   │   ├── 🐍 hospitals.py
│   │   └── 🐍 inventory.py
│   ├── 📁 schemas
│   │   ├── 🐍 hospital.py
│   │   └── 🐍 inventory.py
│   ├── 📁 services
│   │   ├── 🐍 blockchain_client.py
│   │   ├── 🐍 dispatch_service.py
│   │   └── 🐍 gis_client.py
│   └── 🐍 main.py
├── 📁 contracts
│   └── 📄 SanjeevaniEscrow.sol
├── 📁 frontend
│   ├── 📁 artifacts
│   │   ├── 📁 api-server
│   │   │   ├── 📁 .replit-artifact
│   │   │   │   └── ⚙️ artifact.toml
│   │   │   ├── 📁 src
│   │   │   │   ├── 📁 lib
│   │   │   │   │   ├── ⚙️ .gitkeep
│   │   │   │   │   └── 📄 logger.ts
│   │   │   │   ├── 📁 middlewares
│   │   │   │   │   └── ⚙️ .gitkeep
│   │   │   │   ├── 📁 routes
│   │   │   │   │   ├── 📄 health.ts
│   │   │   │   │   └── 📄 index.ts
│   │   │   │   ├── 📄 app.ts
│   │   │   │   └── 📄 index.ts
│   │   │   ├── 📄 build.mjs
│   │   │   ├── ⚙️ package.json
│   │   │   └── ⚙️ tsconfig.json
│   │   ├── 📁 mockup-sandbox
│   │   │   ├── 📁 .replit-artifact
│   │   │   │   └── ⚙️ artifact.toml
│   │   │   ├── 📁 src
│   │   │   │   ├── 📁 .generated
│   │   │   │   │   └── 📄 mockup-components.ts
│   │   │   │   ├── 📁 components
│   │   │   │   │   └── 📁 ui
│   │   │   │   │       ├── 📄 accordion.tsx
│   │   │   │   │       ├── 📄 alert-dialog.tsx
│   │   │   │   │       ├── 📄 alert.tsx
│   │   │   │   │       ├── 📄 aspect-ratio.tsx
│   │   │   │   │       ├── 📄 avatar.tsx
│   │   │   │   │       ├── 📄 badge.tsx
│   │   │   │   │       ├── 📄 breadcrumb.tsx
│   │   │   │   │       ├── 📄 button-group.tsx
│   │   │   │   │       ├── 📄 button.tsx
│   │   │   │   │       ├── 📄 calendar.tsx
│   │   │   │   │       ├── 📄 card.tsx
│   │   │   │   │       ├── 📄 carousel.tsx
│   │   │   │   │       ├── 📄 chart.tsx
│   │   │   │   │       ├── 📄 checkbox.tsx
│   │   │   │   │       ├── 📄 collapsible.tsx
│   │   │   │   │       ├── 📄 command.tsx
│   │   │   │   │       ├── 📄 context-menu.tsx
│   │   │   │   │       ├── 📄 dialog.tsx
│   │   │   │   │       ├── 📄 drawer.tsx
│   │   │   │   │       ├── 📄 dropdown-menu.tsx
│   │   │   │   │       ├── 📄 empty.tsx
│   │   │   │   │       ├── 📄 field.tsx
│   │   │   │   │       ├── 📄 form.tsx
│   │   │   │   │       ├── 📄 hover-card.tsx
│   │   │   │   │       ├── 📄 input-group.tsx
│   │   │   │   │       ├── 📄 input-otp.tsx
│   │   │   │   │       ├── 📄 input.tsx
│   │   │   │   │       ├── 📄 item.tsx
│   │   │   │   │       ├── 📄 kbd.tsx
│   │   │   │   │       ├── 📄 label.tsx
│   │   │   │   │       ├── 📄 menubar.tsx
│   │   │   │   │       ├── 📄 navigation-menu.tsx
│   │   │   │   │       ├── 📄 pagination.tsx
│   │   │   │   │       ├── 📄 popover.tsx
│   │   │   │   │       ├── 📄 progress.tsx
│   │   │   │   │       ├── 📄 radio-group.tsx
│   │   │   │   │       ├── 📄 resizable.tsx
│   │   │   │   │       ├── 📄 scroll-area.tsx
│   │   │   │   │       ├── 📄 select.tsx
│   │   │   │   │       ├── 📄 separator.tsx
│   │   │   │   │       ├── 📄 sheet.tsx
│   │   │   │   │       ├── 📄 sidebar.tsx
│   │   │   │   │       ├── 📄 skeleton.tsx
│   │   │   │   │       ├── 📄 slider.tsx
│   │   │   │   │       ├── 📄 sonner.tsx
│   │   │   │   │       ├── 📄 spinner.tsx
│   │   │   │   │       ├── 📄 switch.tsx
│   │   │   │   │       ├── 📄 table.tsx
│   │   │   │   │       ├── 📄 tabs.tsx
│   │   │   │   │       ├── 📄 textarea.tsx
│   │   │   │   │       ├── 📄 toast.tsx
│   │   │   │   │       ├── 📄 toaster.tsx
│   │   │   │   │       ├── 📄 toggle-group.tsx
│   │   │   │   │       ├── 📄 toggle.tsx
│   │   │   │   │       └── 📄 tooltip.tsx
│   │   │   │   ├── 📁 hooks
│   │   │   │   │   ├── 📄 use-mobile.tsx
│   │   │   │   │   └── 📄 use-toast.ts
│   │   │   │   ├── 📁 lib
│   │   │   │   │   └── 📄 utils.ts
│   │   │   │   ├── 📄 App.tsx
│   │   │   │   ├── 🎨 index.css
│   │   │   │   └── 📄 main.tsx
│   │   │   ├── ⚙️ components.json
│   │   │   ├── 🌐 index.html
│   │   │   ├── 📄 mockupPreviewPlugin.ts
│   │   │   ├── ⚙️ package.json
│   │   │   ├── ⚙️ tsconfig.json
│   │   │   └── 📄 vite.config.ts
│   │   └── 📁 sanjeevani
│   │       ├── 📁 .replit-artifact
│   │       │   └── ⚙️ artifact.toml
│   │       ├── 📁 public
│   │       │   ├── 🖼️ favicon.svg
│   │       │   └── 📄 robots.txt
│   │       ├── 📁 src
│   │       │   ├── 📁 components
│   │       │   │   ├── 📁 ui
│   │       │   │   │   ├── 📄 accordion.tsx
│   │       │   │   │   ├── 📄 alert-dialog.tsx
│   │       │   │   │   ├── 📄 alert.tsx
│   │       │   │   │   ├── 📄 aspect-ratio.tsx
│   │       │   │   │   ├── 📄 avatar.tsx
│   │       │   │   │   ├── 📄 badge.tsx
│   │       │   │   │   ├── 📄 breadcrumb.tsx
│   │       │   │   │   ├── 📄 button-group.tsx
│   │       │   │   │   ├── 📄 button.tsx
│   │       │   │   │   ├── 📄 calendar.tsx
│   │       │   │   │   ├── 📄 card.tsx
│   │       │   │   │   ├── 📄 carousel.tsx
│   │       │   │   │   ├── 📄 chart.tsx
│   │       │   │   │   ├── 📄 checkbox.tsx
│   │       │   │   │   ├── 📄 collapsible.tsx
│   │       │   │   │   ├── 📄 command.tsx
│   │       │   │   │   ├── 📄 context-menu.tsx
│   │       │   │   │   ├── 📄 dialog.tsx
│   │       │   │   │   ├── 📄 drawer.tsx
│   │       │   │   │   ├── 📄 dropdown-menu.tsx
│   │       │   │   │   ├── 📄 empty.tsx
│   │       │   │   │   ├── 📄 field.tsx
│   │       │   │   │   ├── 📄 form.tsx
│   │       │   │   │   ├── 📄 hover-card.tsx
│   │       │   │   │   ├── 📄 input-group.tsx
│   │       │   │   │   ├── 📄 input-otp.tsx
│   │       │   │   │   ├── 📄 input.tsx
│   │       │   │   │   ├── 📄 item.tsx
│   │       │   │   │   ├── 📄 kbd.tsx
│   │       │   │   │   ├── 📄 label.tsx
│   │       │   │   │   ├── 📄 menubar.tsx
│   │       │   │   │   ├── 📄 navigation-menu.tsx
│   │       │   │   │   ├── 📄 pagination.tsx
│   │       │   │   │   ├── 📄 popover.tsx
│   │       │   │   │   ├── 📄 progress.tsx
│   │       │   │   │   ├── 📄 radio-group.tsx
│   │       │   │   │   ├── 📄 resizable.tsx
│   │       │   │   │   ├── 📄 scroll-area.tsx
│   │       │   │   │   ├── 📄 select.tsx
│   │       │   │   │   ├── 📄 separator.tsx
│   │       │   │   │   ├── 📄 sheet.tsx
│   │       │   │   │   ├── 📄 sidebar.tsx
│   │       │   │   │   ├── 📄 skeleton.tsx
│   │       │   │   │   ├── 📄 slider.tsx
│   │       │   │   │   ├── 📄 sonner.tsx
│   │       │   │   │   ├── 📄 spinner.tsx
│   │       │   │   │   ├── 📄 switch.tsx
│   │       │   │   │   ├── 📄 table.tsx
│   │       │   │   │   ├── 📄 tabs.tsx
│   │       │   │   │   ├── 📄 textarea.tsx
│   │       │   │   │   ├── 📄 toast.tsx
│   │       │   │   │   ├── 📄 toaster.tsx
│   │       │   │   │   ├── 📄 toggle-group.tsx
│   │       │   │   │   ├── 📄 toggle.tsx
│   │       │   │   │   └── 📄 tooltip.tsx
│   │       │   │   └── 📄 error-boundary.tsx
│   │       │   ├── 📁 hooks
│   │       │   │   ├── 📄 use-mobile.tsx
│   │       │   │   └── 📄 use-toast.ts
│   │       │   ├── 📁 lib
│   │       │   │   ├── 📝 README.md
│   │       │   │   ├── 📄 api.ts
│   │       │   │   └── 📄 utils.ts
│   │       │   ├── 📁 pages
│   │       │   │   └── 📄 not-found.tsx
│   │       │   ├── 📄 App.tsx
│   │       │   ├── 🎨 index.css
│   │       │   └── 📄 main.tsx
│   │       ├── ⚙️ components.json
│   │       ├── 🌐 index.html
│   │       ├── ⚙️ package.json
│   │       ├── ⚙️ tsconfig.json
│   │       ├── 📄 tsconfig.tsbuildinfo
│   │       └── 📄 vite.config.ts
│   ├── 📁 attached_assets
│   │   ├── 📄 Pasted-Create-a-futuristic-high-end-web-application-UI-for-a-p_1787314413183.txt
│   │   ├── 🖼️ Untitled_design_(1)_1787314419698.png
│   │   ├── 🖼️ WhatsApp_Image_2026-08-21_at_00.03.48_1787314931953.jpeg
│   │   └── 🖼️ download_(55)_1787315213518.jpg
│   ├── 📁 lib
│   │   ├── 📁 api-client-react
│   │   │   ├── 📁 src
│   │   │   │   ├── 📁 generated
│   │   │   │   │   ├── 📄 api.schemas.ts
│   │   │   │   │   └── 📄 api.ts
│   │   │   │   ├── 📄 custom-fetch.ts
│   │   │   │   └── 📄 index.ts
│   │   │   ├── ⚙️ package.json
│   │   │   └── ⚙️ tsconfig.json
│   │   ├── 📁 api-spec
│   │   │   ├── ⚙️ openapi.yaml
│   │   │   ├── 📄 orval.config.ts
│   │   │   └── ⚙️ package.json
│   │   ├── 📁 api-zod
│   │   │   ├── 📁 src
│   │   │   │   ├── 📁 generated
│   │   │   │   │   ├── 📁 types
│   │   │   │   │   │   ├── 📄 healthStatus.ts
│   │   │   │   │   │   └── 📄 index.ts
│   │   │   │   │   └── 📄 api.ts
│   │   │   │   └── 📄 index.ts
│   │   │   ├── ⚙️ package.json
│   │   │   └── ⚙️ tsconfig.json
│   │   └── 📁 db
│   │       ├── 📁 src
│   │       │   ├── 📁 schema
│   │       │   │   └── 📄 index.ts
│   │       │   └── 📄 index.ts
│   │       ├── 📄 drizzle.config.ts
│   │       ├── ⚙️ package.json
│   │       └── ⚙️ tsconfig.json
│   ├── 📁 scripts
│   │   ├── 📁 src
│   │   │   └── 📄 hello.ts
│   │   ├── ⚙️ package.json
│   │   ├── 📄 post-merge.sh
│   │   └── ⚙️ tsconfig.json
│   ├── ⚙️ .gitignore
│   ├── ⚙️ .npmrc
│   ├── ⚙️ .replit
│   ├── ⚙️ .replitignore
│   ├── ⚙️ package.json
│   ├── ⚙️ pnpm-lock.yaml
│   ├── ⚙️ pnpm-workspace.yaml
│   ├── 📝 replit.md
│   ├── ⚙️ tsconfig.base.json
│   └── ⚙️ tsconfig.json
├── 📁 ignition
│   └── 📁 modules
│       └── 📄 Sanjeevani.ts
├── 📁 listeners
│   └── 📄 eventListener.ts
├── 📁 mcp_server
│   ├── 🐍 __init__.py
│   ├── 🐍 agent.py
│   ├── 🐍 api.py
│   ├── 🐍 blockchain_tools.py
│   ├── 🐍 client.py
│   ├── 🌐 index.html
│   ├── 🐍 main.py
│   └── 🐍 wrapper.py
├── 📁 primary
│   ├── 📁 data
│   │   ├── 📁 processed
│   │   │   ├── ⚙️ .gitkeep
│   │   │   ├── 📄 hospital_state_summary.csv
│   │   │   ├── 📄 hospitals_by_position.csv
│   │   │   └── 📄 processed_hospitals.csv
│   │   ├── 📁 raw
│   │   │   ├── ⚙️ .gitkeep
│   │   │   └── 📄 hospital_directory.csv
│   │   └── 📁 visualization
│   │       ├── ⚙️ .gitkeep
│   │       └── 🌐 hospital_map.html
│   ├── 📁 docs
│   │   ├── 🖼️ ERD.png
│   │   ├── 📄 WalkThrough.txt
│   │   ├── 📝 buildplan.md
│   │   └── 🖼️ landing_pg.jpeg
│   └── 📁 notebooks
│       └── 📄 abdm_DATA_INSPECT.ipynb
├── 📁 scripts
│   ├── 📄 config.ts
│   ├── 📄 confirmDelivery.ts
│   ├── 📄 createLoan.ts
│   ├── 📄 deploy.ts
│   ├── 📄 markReturned.ts
│   ├── 📄 registerEquipment.ts
│   └── 📄 settleLoan.ts
├── 📁 test
│   └── 📄 Counter.ts
├── 📁 visuals
│   ├── 📄 chat.js
│   └── 🌐 index.html
├── ⚙️ .gitignore
├── 📄 hardhat.config.ts
├── 🌐 isochrone_map.html
├── ⚙️ package-lock.json
├── ⚙️ package.json
├── ⚙️ pnpm-lock.yaml
├── ⚙️ pnpm-workspace.yaml
├── 📄 requirements.txt
├── 🌐 route_map.html
└── ⚙️ tsconfig.json
```

---
*Generated by FileTree Pro Extension*