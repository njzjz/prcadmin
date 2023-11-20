# 统计用区划代码和城乡划分代码

## 数据

[`current.csv`](current.csv)为2023年的最新数据。

[`patches`](patches)文件夹给出了2022年-2023年的历年变更，以patch文件储存。对最新数据应用patch时，需要使用`--reverse`：

```sh
git apply --reverse patches/2023.patch
```

## 下载脚本

需要Python 3.9或以上版本。

```sh
pip install -r requirements.txt
python prcadmin.py -y 2023 -f 2023.csv
python sort_csv.py 2023.csv 2023_sort.csv
```

## 版权声明

所有统计数据版权归国家统计局所有，根据[国家统计局网站服务条款](http://www.stats.gov.cn/wzgl/202302/t20230217_1912857.html)以资料性公共免费信息为使用目的的合理、善意引用。如二次使用，亦需遵守该网站的服务条款。

除数据以外的其它所有文件以[GNU Lesser General Public License v3.0 or later](https://spdx.org/licenses/LGPL-3.0-or-later.html)协议授权。