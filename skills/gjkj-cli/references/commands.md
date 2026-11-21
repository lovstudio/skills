# 常用命令

`G="python3 $SKILL_DIR/scripts/gjkj_cli.py"`。完整清单 `$G ops`，单个命令的参数 `$G run -- <command> --help`。
查询参数用同名选项（下划线写成连字符），请求体用 `--data '<json>'` 或 `--data @file.json`。默认只输出响应的 `data`，`--envelope` 输出完整 `{code, message, data}`。

## 只读（标 V 的已用真实密钥实测过）

| 想知道 | 命令 | 常用参数 |
| --- | --- | --- |
| 可用区域 | `storage-get-regions` | — |
| 设备资源（卡型、规格，建任务时的 `resources[].mark` 来自这里） | `deployment-resource-search` | — |
| 弹性部署任务列表 | `deployment-task-search`（旧版）/ `task-deployment-search`（新版） | `--status` `--search-value` `--page` `--page-size` |
| 任务详情 | `deployment-task-detail` / `task-deployment-detail` | `--task-id` |
| 任务节点与日志 | `deployment-task-points`、`deployment-task-point-log`、`deployment-task-pod-event` | `--task-id` 等，见 `--help` |
| Job 任务 / 队列 | `task-job-search`、`job-queue-search`、`job-queue-group-search` | `--status` `--page` |
| 账单（按时间） | `billing-get-billing-record` | `--range`（必填）`--start-time` `--end-time`（RFC3339）`--task-ids` |
| 按任务的账单 | `billing-get-task-billing-record` | 见 `--help` |
| 对象存储资源 | `storage-get-storage`、`storage-storage-info` | — |
| 集群存储卷 | `storage-nas-v1-list`、`storage-nas-v1-summary`、`storage-nas-v1-dictionaries` | `--regions` `--statuses` `--page-size`（≤100） |
| 裸金属可购 / 已购 / 订单 | `output-v2-device-output-page-list-product-single-v2`、`…-network-v2`、`output-v2-device-order-get-order-list-v2` | `--data '{}'`（POST 查询） |
| 大模型可用模型 | `llm-list-models` | 需大模型 API Key 且账户有余额 |

## 写操作（W，逐次确认）

| 动作 | 命令 |
| --- | --- |
| 创建 / 修改弹性部署任务 | `deployment-task-create`、`deployment-task-update`、`task-deployment-create`、`task-deployment-update` |
| 暂停 / 恢复 / 停止任务 | `deployment-task-pause`、`deployment-task-recover`、`deployment-task-stop` |
| 改节点数 | `deployment-task-change-points`（如 `--data '{"task_id":388,"points":1}'`） |
| 删除 Pod | `deployment-task-delete-pod` |
| Job 任务与队列 | `task-job-create`、`task-job-stop`、`job-queue-create`、`job-queue-update`、`job-queue-stop`、`job-queue-encrypt-push`（E）、`job-queue-group-stops` |
| 镜像预热 | `task-image-preheat-create`、`…-update`、`…-stop` |
| 存储 | `storage-encrypt-create`（E）、`storage-nas-v1-create`、`…-expand`、`…-delete`、`…-rename`、S3 互传与 SFTP 系列、`storage-release`、`storage-delete` |
| 裸金属下单与续费 | `output-v2-device-order-buy-v2`、`output-v2-auto-renew-device-config-set-auto-renew-config`、`…-delete-auto-renew-config` |

会产生费用的（创建任务、扩容、开存储、购买裸金属、续费）先复述规格与预计费用，再拿用户原话的同意。

## 计费调用（$）

`llm-chat-completions`：按 token 扣账户余额。先 `--dry-run` 给用户看请求体（模型、消息、max_tokens），同意后再发。

## 加密接口（E）

7 个接口要求请求体用平台公钥加密（`job-queue-encrypt-push`、`storage-encrypt-check`、`storage-encrypt-create`、
`storage-encrypt-update`、`storage-nas-v1-encrypt-s3-create`、`storage-nas-v1-encrypt-s3-retry`、`storage-nas-v1-encrypt-s3-check`），
需要 `SUANLI_PLATFORM_PUBLIC_KEY_FILE`；SDK 按 244 字节分段加密后再签名。
