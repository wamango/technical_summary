package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 基本的实现计算奖金的类，也是被装饰器装饰的对象
 *
 * @author dzm
 * @create 2018-11-21 10:49
 **/
public class ConcreteComponent extends Component {
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
        //只是一个默认的实现，默认没有奖金
        return 0;
    }
}
