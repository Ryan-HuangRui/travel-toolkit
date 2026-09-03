# Travel Toolkit

一个开源的 Codex 插件：从旅行规划、每日路线核验，到出发前和旅途中的陪伴式提醒，围绕同一份可移植的行程资料工作。

[English README](README.md)

## 工作流

```text
旅行想法 → plan-travel-guide → Travel Plan Bundle（trip.json）
                                  ↑
                    travel-maps-planner 核验地点与路线
                                  ↓
                             trip-buddy
             文化卡 / 行前准备 / 当日简报 / 异常关注
                                  ↓
                            travel-notify
                                  ↓
                    可选的通知平台适配器（先支持飞书 CLI）
```

`trip.json` 是唯一的行程事实来源。地图服务提供带时效的地点与路线证据；Trip Buddy 读取最新的 Bundle，但不会在未明确确认的情况下改写已确定的行程。

## 包含的技能

- `plan-travel-guide`：探索目的地、确定行程骨架、生成并校验可移植的 Travel Plan Bundle。
- `travel-maps-planner`：通过 Google Maps 或高德地图统一地点信息、核验路线。
- `trip-buddy`：统筹出发前的内容、行前准备、行程中的日间简报与经核实的异常事件。
- `travel-culture-card`、`travel-readiness`、`travel-day-brief`、`travel-disruption-watch`：Trip Buddy 所调用的四类专用内容技能。
- `travel-notify`：与平台无关的通知请求与幂等性边界。
- `travel-notify-feishu-cli`：可选的飞书 IM 机器人适配器，默认只 dry-run，不会发送消息。

## 地图服务

Google Maps 是面向全球行程的默认服务。高德地图适用于中国大陆的 POI 和路线；其国内 Web Service 使用 GCJ-02 坐标。高德海外服务需要单独开通，并使用 WGS84 坐标；适配器必须显式传入 `--international`，以防止不同坐标系被意外混用。

密钥只应保存在本地环境中：

```bash
export GOOGLE_MAPS_API_KEY=...
export AMAP_API_KEY=...
```

不要提交 API Key、收件人配置、预订编号、精确的私人住址，或真实行程导出文件。集成配置见 [docs/integrations.md](docs/integrations.md)。

## 通知

工具包核心只生成经过校验的通知请求，不会自行发送。飞书适配器要求：本机已配置 `lark-cli` 机器人、私有的收件人 profile 映射、明确的用户授权、`state: "sending"`，以及稳定的幂等键。文档发布与消息投递被刻意设计为两个独立的适配层。

## 开发与校验

仓库内的 `examples/synthetic-city-break/` 是一份虚构的示例 Bundle。发布前可运行以下检查：

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/travel-toolkit
python3 plugins/travel-toolkit/skills/plan-travel-guide/scripts/validate_trip.py examples/synthetic-city-break
python3 plugins/travel-toolkit/skills/travel-notify/scripts/validate_notification_request.py plugins/travel-toolkit/skills/travel-notify/references/notification-request.example.json
```

本仓库是源码包。正式发布或提交至插件目录前，建议先通过本地 marketplace 安装并测试。

## 许可证

Apache-2.0。此项目为独立软件，与 Google、高德、飞书/Lark 或 OpenAI 没有隶属关系。
