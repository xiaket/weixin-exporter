## weixin-exporter

导出微信聊天记录, 并展示成一个md文件.


### 简要使用说明

1. 用iFunbox把微信的聊天记录复制到电脑, 修改脚本中对应的值:

    ```
    WX_DATA_DIR = os.path.expanduser('~/.weixin/Documents')
    ```

2. 解压微信的ipa文件, 把这个app复制出来, 修改脚本中对应的值:

    ```    
    WX_APP_DIR = os.path.expanduser('~/.weixin/MicroMessenger.app')
    ```
    
3. 用sqlite找到对应的session id, 修改脚本中对应的值.

    ```
    SESSION = "bf335f0598e916b3cfc710f813bc6b9c"
    ```


