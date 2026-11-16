# Android 组件下载接入

这里同步组件下载、签名验证和资源安装所需的五个公共 Java 类，不包含 QuietTV 桌面界面或完整 Android 应用工程。代码来自已在 QuietTV 2.0.0 / 626 集成的实现；来源提交及逐文件摘要记录在 [source.json](source.json)。

## 下载行为

- 清单与 ZIP 采用同一镜像顺序：`ghfast.top`、`gh-proxy.com`、`v4.gh-proxy.org`、GitHub 原站，失败自动切换，最多两轮。
- 清单采用 40 秒请求预算，比较最多两份有效签名清单的 revision。单次连接、首字节和后续读取的超时设为 8 秒。
- ZIP 临时文件按签名清单中的 SHA-256 命名，手动重试或进程重启后可以继续相同资源。旧版按随机任务编号命名的临时文件不自动参与续传。
- 仅在 HTTP 206 和 Content-Range 与本地偏移、签名大小匹配时追加。服务器返回完整 HTTP 200 时重新写入，避免错误拼接。
- 保留 RSA 签名、最低 revision、原站 URL 限制、ZIP 及逐文件大小和 SHA-256 校验。签名清单仍保存标准 GitHub 地址，镜像映射只发生在传输层。
- 取消会断开当前连接；未完成文件保留供下次继续。下载不会自动切换壁纸。

## 接入宿主

1. 将 `src/main/java/home/quiet/components/` 下五个类加入 Android 宿主的 Java 源集。组件下载面向 Android API21 及以上；宿主仍须按原有设备条件判断天气功能是否可用。
2. 将仓库中的 [public-key.der](../../app/src/main/assets/components/public-key.der) 复制到宿主 `app/src/main/assets/components/public-key.der`。只复制公钥，天气材质继续通过 ZIP 按需下载。
3. 宿主需要 AndroidX Core 的 `AtomicFile` 和 Bouncy Castle 的 Base64 实现。参考宿主已使用 `androidx.core:core:1.12.0`、`org.bouncycastle:bcprov-jdk15to18:1.86`；`org.json` 使用 Android 平台实现。保持宿主现有依赖约束。
4. 在用户确认下载时调用 `ComponentRepository.get(context).start("weather")`；使用 `add` / `remove` 注册和注销状态监听，`state("weather")` 读取状态，`cancel("weather")` 取消。`refresh()` 只更新组件信息，不下载 ZIP。
5. `resources("weather").file(name)` 只返回已验证资源。宿主自行提供进度界面和启用壁纸的交互。支持显示 `message` 中的切源、重试、继续下载提示。

主程序更新器应引用同一份 `DownloadSources`，不要另行维护镜像地址：

```java
static final String[] SOURCES = home.quiet.components.DownloadSources.values();
// 在现有 URL 校验中复用镜像域名判断：
boolean mirrored = home.quiet.components.DownloadSources.mirror(host);
```

该目录不是独立 APK，源码复制后需通过宿主 Android 构建验证。下载状态接口保留既有天气/组网组件兼容；本仓库发布的资源仍仅为电视天气组件。

## 验证

```sh
python3 scripts/validate_android_client.py --output output/android-client-check
```

此命令在仓库根目录运行，需要 JDK 11 或以上。首次运行会从 Maven Central 获取固定版本的 JSON / Bouncy Castle 依赖并验证 SHA-256。它核对五个导出源文件与公钥摘要，编译不依赖 Android 平台的四个核心类；不代替宿主 Android 构建或电视端下载测试。

同步前，宿主完成了 32 项本地专项测试、benchmark APK 构建及索尼同签名覆盖安装。专项测试覆盖断流切源、重启续传、服务器忽略 Range、错误范围/长度、签名和哈希失败、取消、非法重定向等。索尼真实网络中的各镜像、完整 ZIP 和跨重启续传由用户后续手动验收。

## 资源版本

本次只同步接入源码和说明。`weather-v1.0.0` 的 ZIP、签名清单、公钥和附件校验文件保持原字节，无需为下载逻辑重新发布天气资源。
