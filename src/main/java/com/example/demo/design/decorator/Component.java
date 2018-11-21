package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 计算奖金的组件接口
 *
 * @author dzm
 * @create 2018-11-21 10:46
 **/
public abstract class Component {

    /**
     * 计算某人在某段时间内的奖金
     * @param user 被计算奖金的人员
     * @param begin 计算奖金的开始时间
     * @param end 计算奖金的结束时间
     * @return
     */
    public abstract double calcPrize(String user, Date begin,Date end);
}
