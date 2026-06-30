name: Bug Report
description: 报告一个 bug
labels: ["bug"]
body:
  - type: textarea
    id: what
    attributes:
      label: 发生了什么
      description: 简明描述 bug
    validations:
      required: true

  - type: textarea
    id: repro
    attributes:
      label: 复现步骤
      description: 一步步怎么操作能复现
    validations:
      required: true

  - type: textarea
    id: expect
    attributes:
      label: 期望结果
      description: 你期望发生什么
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: 实际结果
      description: 实际发生了什么, 贴错误日志/截图
    validations:
      required: true

  - type: input
    id: env
    attributes:
      label: 部署环境
      description: 例如 "OrbStack 1.0 / Mac M2 / Docker 24.0"
    validations:
      required: false
