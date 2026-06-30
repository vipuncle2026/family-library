name: Feature Request
description: 提出一个新功能
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: 想解决什么问题
      description: 你在管理家庭藏书时遇到的痛点
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 你想要的方案
      description: 描述你期望的功能和交互
    validations:
      required: true

  - type: textarea
    id: alt
    attributes:
      label: 备选方案
      description: 是否考虑过其他做法? 有什么 trade-off?
    validations:
      required: false
