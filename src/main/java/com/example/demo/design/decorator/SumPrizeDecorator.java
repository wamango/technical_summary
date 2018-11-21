package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 装饰器对象，计算累计奖金
 *
 * @author dzm
 * @create 2018-11-21 10:59
 **/
public class SumPrizeDecorator extends Decorator {
    /**
     * 通过构造方法传入被装饰的对象
     *
     * @param c 被装饰的对象
     */
    public SumPrizeDecorator(Component c) {
        super(c);
    }

    /**
     * 计算某人在某段时间内的奖金
     *
     * @param user  被计算奖金的人员
     * @param begin 计算奖金的开始时间
     * @param end   计算奖金的结束时间
     * @return
     */
    @Override
    public double calcPrize(String user, Date begin, Date end) {
        //先获取前面运算的奖金
        double money = super.calcPrize(user, begin, end);
        //计算累计奖金，按人员和时间去获取累计业务额，然后再乘以0.1%
        //假定所有的累计金额业务额都是1000000元
        double prize = 1000000*0.001;
        System.out.println(user+"累计奖金："+prize);
        return money+prize;
    }
}
