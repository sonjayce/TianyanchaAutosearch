import os
import csv
import sys

def main():
    # 构建文件路径
    input_file = os.path.join('result', 'result.csv')
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：未找到文件 {input_file}（请确认result目录存在且包含result.csv）")
        return

    # 检测列名并获取索引
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("错误：CSV文件为空")
            return
        
        # 查找域名列（支持中英文列名）
        column_names = ['domain', '网站域名']
        domain_col = None
        for col in column_names:
            if col in headers:
                domain_col = headers.index(col)
                break
        
        if domain_col is None:
            print("错误：未找到域名列（请确认列名为 'domain' 或 '域名'）")
            return

    # 获取总行数用于进度计算
    with open(input_file, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f) - 1  # 排除标题行

    domains = []
    processed = 0

    # 读取并处理数据
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        
        print("处理进度：")
        for row in reader:
            processed += 1
            domain = row[domain_col].strip()
            
            # 更新进度条
            progress = processed / total_lines * 100
            bar_length = 30
            filled = int(bar_length * processed // total_lines)
            bar = '█' * filled + '-' * (bar_length - filled)
            sys.stdout.write(f"\r[{bar}] {progress:.1f}%")
            sys.stdout.flush()
            
            if domain:
                domains.append(f'domain="{domain}"')

    # 生成结果并保存
    if not domains:
        print("\n警告：未找到有效域名")
        return

    result = "||".join(domains)  # 关键修改点
    with open('fofa.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"\n完成！共处理 {processed} 行，找到 {len(domains)} 个域")
    print(f"\n完成！生成 {len(domains)} 个OR条件表达式")
    print("结果已保存到 fofa.txt")

if __name__ == "__main__":
    main()