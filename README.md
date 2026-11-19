# Codex 后台任务

AstrBot 管理员可让 Bot 将编程任务提交给 Codex CLI。任务独立运行，结果写入持久化目录，完成后主动回传原会话。

LLM 工具：`codex_task_submit`、`codex_task_status`、`codex_task_stop`、`codex_task_resume`。

任务项目目录位于 `data/codex-projects/<项目ID>`，任务记录位于 `data/plugin_data/astrbot_plugin_codex_tasks`。仅 AstrBot 管理员可以提交、查询、停止和恢复任务。

`/codex任务` 按模板显示最近任务，也可用 `/codex任务 <任务ID>` 查看单项。在插件配置的“自定义排版模板”文本框中编辑整体布局，支持直接换行。变量：`${任务ID}`、`${项目}`、`${状态}`、`${状态码}`、`${创建时间}`、`${摘要}`、`${输出}`、`${错误}`、`${退出码}`。默认每条摘要最多 240 字，列表最多 5 条；未知变量会回退默认模板。旧版 `{id}` 等格式仍兼容。
