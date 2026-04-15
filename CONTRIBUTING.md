# Contributing to HydroponicOne

First off, thank you for considering contributing to HydroponicOne! It's people like you that make HydroponicOne such a great tool for the hydroponics community.

## 🚀 How Can I Contribute?

### Reporting Bugs
- Use the GitHub Issue Tracker.
- Describe the bug and include steps to reproduce.
- Mention your hardware setup (ESP32 type, sensors used).

### Suggesting Enhancements
- Open an issue with the "feature request" tag.
- Explain why the feature would be useful.

### Pull Requests
1. Fork the repo and create your branch from `main`.
2. Hardware changes? Update `docs/02_HARDWARE_SETUP.md`.
3. Firmware changes? Ensure code is compatible with the modular sensor architecture.
4. UI changes? Maintain the glassmorphism aesthetic.
5. Create a PR with a clear description of your changes.

## 🛠️ Development Environment

### Firmware
- We use **PlatformIO**.
- Please run `pio run` to verify compilation before submitting.

### Backend
- Node.js + Fastify + Prisma.
- Run `npm test` (if applicable) and ensure `npx prisma generate` is run after schema changes.

### Frontend
- React + Vite + Tailwind CSS.
- Keep components small and focused.

### Hardware (PCB & 3D Design)
HydroponicOne is a physical system, and hardware contributions are highly encouraged!
- **PCBs / Schematics**: Please submit designs in KiCad format. Include gerber files for easy viewing.
- **3D Printed Parts**: If contributing sensor mounts or waterproof enclosures, please provide `.STL` files and ideally the original CAD files (STEP, Fusion360, FreeCAD) so others can modify them.
- Ensure all 3D designs mention the recommended material (e.g., PETG or ABS for UV/water resistance versus PLA).

## ⚖️ Code of Conduct
Please be respectful and patient. We are a community of growers and developers helping each other.

---

Built with ❤️ for sustainable farming.
