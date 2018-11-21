package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 装饰器对象，计算当月团队业务奖金
 *
 * @author dzm
 * @create 2018-11-21 10:59
 **/
public class GroupPrizeDecorator extends Decorator {
    /**
     * 通过构造方法传入被装饰的对象
     *
     * @param c 被装饰的对象
     */
    public GroupPrizeDecorator(Component c) {
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
        //计算团队业务奖金，先计算出团队总的业务额，然后再乘以1%
        double group = 0.0;
        for (double d : TempDB.mapMonthSaleMoney.values()){
            group+=d;
        }
        double prize = group*0.01;
        System.out.println(user+"当月团队业务奖金："+prize);
        return money+prize;
    }
}
