package com.example.demo.design.decorator;

/**
 * 客户端-java中io流就用了装饰器模式
 *
 * @author dzm
 * @create 2018-11-21 11:15
 **/
public class Client {
    public static void main(String[] args) {
        //先创建计算基本奖金的类，这也是被装饰的对象
        Component component = new ConcreteComponent();
        //然后对计算的基本奖金进行装饰，这是要组合各个装饰
        //说明，各个装饰者之间最好不要有先后顺序的限制

        //先组合普通业务人员的奖金计算
        Decorator d1 = new MonthPrizeDecorator(component);
        Decorator d2 = new SumPrizeDecorator(d1);

        //用最后组装好的业务对象调用
        double zs = d2.calcPrize("张三",null,null);
        System.out.println("========张三应得奖金："+zs);
        double ls = d2.calcPrize("李四",null,null);
        System.out.println("========李四应得奖金："+ls);

        //如果是业务经理，计算团队奖金
        Decorator d3 = new GroupPrizeDecorator(d2);
        double ww = d3.calcPrize("王五",null,null);
        System.out.println("========王五应得奖金："+ww);
    }
}
