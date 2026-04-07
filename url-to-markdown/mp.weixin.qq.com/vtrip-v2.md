---
url: https://mp.weixin.qq.com/s/SZjMamBRCMBKV35ZqPRj2A
title: "VTrip：一键生成你的城市旅游轨迹"
author: "南川同学"
captured_at: "2026-04-04T16:55:10.369Z"
---

# VTrip：一键生成你的城市旅游轨迹

作为 P 人，两年前我曾经漫无目的地在大地上漂泊，三个月内途径了： 北京、武汉、咸宁、长沙、南宁、柳州、桂林、广州、东莞、惠州、深圳 、香港、杭州。

而今年春节以来的一个月内，我一下子遍访了20个城市，这次的目的略有不同，主要以创业的前辈以及好久未见的旧朋友为主，收获颇多。路线如下：1. 常州 2. 无锡 3. 苏州 4. 上海 5. 杭州 6. 广州 7. 香港 8. 深圳 9. 广州 10. 昆明 11. 曲靖 12. 成都 13. 重庆 14. 长沙 15. 武汉 16. 合肥 17. 南京 18. 上海 19. 泰安 20. 济南 21. 北京。

这一次本来还想继续走一下心心念的大西北和大东北，但实在时间、预算有限，北京的朋友们也希望我尽早回京进入工作状态。所以，只能下次了！

我还需要一点时间以整理出旅后感，并决定**周日晚上在北京五道口举办一场线下闭门分享会**，欢迎留言区与后台申请打卡交流~

好了，回到本文写作的初衷，由于本次旅行城市过多，我很想可视化我的旅行足迹，问了一下 DeepSeek，它给我推荐了一些方案。

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMLbxQItYlgaLLckw9GeNOsGtaqOvnbToiaOjXqxEsxBKW1TmwFG08Eiag/640?wx_fmt=png&from=appmsg#imgIndex=0)image.png

其中西瓜足迹小程序已经搜索不到，而足迹地图小程序只能显示点亮效果，不能看到访问城市的顺序。

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_jpg/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMu4NQxIIjjakVwgd2dpc4I8HjC2s8VE9GSicGbWiaNGjicqvH2s4U0ibiaUA/640?wx_fmt=jpeg&from=appmsg#imgIndex=1)image.png

所以我就想到用 AI 给我快速开发一个能显示轨迹的产品，无非就是：

1. 数据系统
2. 支持增量录入
3. 支持一次性导入导出
4. 支持城市、日期、交通工具等数据结构

可视化系统

1. 支持一张风格化的地图
2. 支持突出显示遍访的城市
3. 支持友好地显示城市的访问顺序
4. 支持更酷的交通展示方式（例如高铁可以基于列车号展示沿途结点，飞机则可以像航旅纵横一样显示一条弧线）

支持分享……

……

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMnHffT0Z24QCqKn7UNoficXIDIhFhNr3IhFlhUKtN2toqaqwULJqvzjg/640?wx_fmt=png&from=appmsg#imgIndex=2)image.png

基于此，我就让 AI 开工了。

我本来是只用 Windsurf 的，但无奈中途经常 internal error，这背后的原因有很多种，比如说：

- 目前用的人太多了，比较卡，后端没有做很好的队列系统（这点为字节打 call）……
- 目标代码文件过长，导致处理起来出现问题……

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMzxAGU8GicAIIrZEUnibqUkwa8lAkn9eLZicAp886xB0Bk9zOVFvE8UrLA/640?wx_fmt=png&from=appmsg#imgIndex=3)image.png

所以我顺带尝试了字节的 Trae。

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMeq0JYRicRb6ibyJb2RTQ59Szb9SDwaZiaB72dVAbqVzjq0ChOb6tSmwmQ/640?wx_fmt=png&from=appmsg#imgIndex=4)image.png

实测下来，我觉得 Trae 目前比较优越的点有三个：

1. 对大模型的 api 调用做了队列控制，从产品体验上更 stable，可预期未来开付费高速通道后体验会更好
2. 内置了 web browser，非常适合前端开发项目（等于降维打击了 bolt）
3. 免费（当然，我不是很关心这个，但目前这个也很重要）

但最大的缺点还是慢，用的人太多了，尤其是我是通宵写的程序，在快天亮的时候，直接排队到离谱了（能达到 60 多……），这对我这样的专业开发者来说是很难接受的。

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMstLF002Z49VAXNlKcUhicWeYzt0iaIPIU7IhEW7icwUoagzM4QYrXdbCQ/640?wx_fmt=png&from=appmsg#imgIndex=5)image.png

不过有一说一，Trae 对专业开发者来说，目前的优势有限，因为 AI IDE 的核心是给一个需求后它实现的好不好，在这点上，Trae 做的暂时并不会比 windsurf、cursor 等更好，但普通人确实无法抵挡它免费与稳定可靠的诱惑！

希望 Trae 继续加油，这是他们的 Discord：https://discord.com/invite/NV3MF24tAe

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMZZjF6qgyO2fCYY4TW9Z8xJgbPzicVHMPy0h97UicH5aPRXrBauLx2nKg/640?wx_fmt=png&from=appmsg#imgIndex=6)image.png

ok，说回正事，我最后和 AI 共同开发出的可视化城市轨迹系统长这样：

![image.png](https://mmbiz.qpic.cn/sz_mmbiz_png/2niaYkVLHpnGAYl9ibjMvdv0RfWS31lAgMktWHQ9icXibxhW7dv9ZMGIlAgib15DCES3auge8UgCzUofVKo2lB4ZatA/640?wx_fmt=png&from=appmsg#imgIndex=7)image.png

目前免费，快来试试吧：**vtrip.cs-magic.cn** ！

正在迭代中，已经给设计师加鸡腿，以设计更酷的地图与轨迹！

我的产品哲学：我所想要的，我就创造它。

我的产品合集：http://m.mrw.so/6hE9Ni

![图片](https://mmbiz.qpic.cn/sz_mmbiz_gif/2niaYkVLHpnGI7oTqr1SPDbWJH43RJ5CTRWXHiaFTmnwgxJMrzzEHbpoCsXZqzjWYYFia8pGtt2M9WPnd3041ZyMg/640?wx_fmt=gif&from=appmsg#imgIndex=9)

欢迎持续关注我的产品奥德赛之旅！

感兴趣的话也可以加入我的 AI 交流社群！

2025，与手工川一起成长，让 AI 助力您的发展！