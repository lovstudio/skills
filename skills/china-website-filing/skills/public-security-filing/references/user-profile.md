# User Profile contract

本模块使用 Kit 根目录的 [user-profile/v1 contract](../../../references/user-profile.md) 和 `skills.lov-public-security-filing` 命名空间。

每次运行按当前请求、项目上下文、Skill 记录、共享偏好、品牌/用户 Profile、安全默认值的顺序解析。只有用户直接说明且希望长期复用的非敏感事实才可通过 `$KIT_DIR/scripts/profile_store.py` 持久化；证件、手机号、验证码、Cookie、密钥和扫描件不得保存。

