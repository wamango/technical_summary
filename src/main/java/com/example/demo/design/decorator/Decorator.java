package com.example.demo.design.decorator;

import java.util.Date;

/**
 * 装饰器的接口，需要和被装饰的对象实现同样的接口
 *
 * @author dzm
 * @create 2018-11-21 10:56
 **/
public abstract class Decorator extends Component {

    /**
     * 持有被装饰的组件对象
     */
    protected Component c;

    /**
     * 通过构造方法传入被装饰的对象
     * @param c 被装饰的对象
     */
    public Decorator(Component c) {
        this.c = c;
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
        //转调组件对象的方法
        return c.calcPrize(user, begin, end);
    }
}
