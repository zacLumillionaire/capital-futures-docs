#!/usr/bin/env python3
# 修復縮排問題

def fix_mdd_gui_indentation():
    """修復 mdd_gui.py 的縮排問題"""
    
    # 讀取文件
    with open('mdd_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到問題區域並重新寫入正確的縮排
    fixed_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # 修復第974-982行的縮排
        if line_num == 974:
            fixed_lines.append("        for time_interval in time_intervals:\n")
        elif line_num == 975:
            fixed_lines.append("            for l1_sl in lot1_stop_loss:\n")
        elif line_num == 976:
            fixed_lines.append("                for l2_sl in lot2_stop_loss:\n")
        elif line_num == 977:
            fixed_lines.append("                    for l3_sl in lot3_stop_loss:\n")
        elif line_num == 978:
            fixed_lines.append("                        for tp_combination in all_take_profit_combinations:\n")
        elif line_num == 979:
            fixed_lines.append("                            for l1_tp in tp_combination['lot1']:\n")
        elif line_num == 980:
            fixed_lines.append("                                for l2_tp in tp_combination['lot2']:\n")
        elif line_num == 981:
            fixed_lines.append("                                    for l3_tp in tp_combination['lot3']:\n")
        elif line_num == 982:
            fixed_lines.append("                                        try:\n")
        else:
            fixed_lines.append(line)
    
    # 寫回文件
    with open('mdd_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ 縮排修復完成")

if __name__ == "__main__":
    fix_mdd_gui_indentation()
