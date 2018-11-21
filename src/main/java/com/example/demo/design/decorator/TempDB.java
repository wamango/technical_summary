package com.example.demo.design.decorator;

import java.util.HashMap;
import java.util.Map;

/**
 * 在内存中模拟数据库吗，准备点测试数据，好计算奖金
 *
 * @author dzm
 * @create 2018-11-21 11:04
 **/
public class TempDB {
    public TempDB() {
    }

    public static Map<String,Double> mapMonthSaleMoney = new HashMap<>();

    static {
        //填充数据
        mapMonthSaleMoney.put("张三",1000.0);
        mapMonthSaleMoney.put("李四",2000.0);
        mapMonthSaleMoney.put("王五",3000.0);

    }
}
