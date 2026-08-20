# Frontend structure

The frontend is organized by responsibility and visual scope:

- `windows/`: top-level `QMainWindow` and `QDialog` classes. Windows compose widgets and coordinate user flows.
- `widgets/common/`: visual controls reused by unrelated features.
- `widgets/<feature>/`: visual controls owned by one feature or window area.
- `components/`: reusable non-visual behavior, including `QObject` tasks, data loading, and presentation formatting.
- `clients/`: backend HTTP requests and response validation.
- `models/`: frontend-only data models.
- `utils/`: small, stateless, cross-cutting helpers such as theme and path resolution.
- `assets/`: icons, help pages, and other packaged static files.

Dependencies should generally point inward from windows to widgets, components, and clients. Widgets may use components, models, and utilities, while components should not create or own widgets.
