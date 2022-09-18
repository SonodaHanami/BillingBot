# BillingBot
记账bot

## 使用方法
克隆本仓库
```sh
git clone https://github.com/SonodaHanami/BillingBot.git
cd BillingBot
```
复制一份配置文件并修改
```sh
cp default-config.py config.py
```
安装screen
```sh
apt install screen
```
创建一个新的screen
```sh
screen -S billing
```
在screen中运行
```sh
python3 -u run.py
```
使用组合键`Ctrl-a d`离开screen

再次回到这个screen
```sh
screen -r billing
```