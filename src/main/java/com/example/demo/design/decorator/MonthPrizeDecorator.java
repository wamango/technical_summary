package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 装饰器对象，计算当月业务奖金
 *
 * @author dzm
 * @create 2018-11-21 10:59
 **/
public class MonthPrizeDecorator extends Decorator {
    /**
     * 通过构造方法传入被装饰的对象
     *
     * @param c 被装饰的对象
     */
    public MonthPrizeDecorator(Component c) {
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
        //计算当月业务奖金，按人员和时间去获取当月业务额，然后再乘以3%
        double prize = TempDB.mapMonthSaleMoney.get(user)*0.03;
        System.out.println(user+"当月业务奖金："+prize);
        return money+prize;
    }
}
