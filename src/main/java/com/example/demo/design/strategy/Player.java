package com.example.demo.design.strategy;

import lombok.Data;

@Data
public class Player {

    //玩家消费总额
    private Double totalAmount = 0D;

    //玩家单次消费金额
    private Double amount = 0D;

    //每个玩家都有一个计算价格的策略，初始值
    private CalPrice calPrice = new Orgnic();

    /**
     * 客户购买东西，增加总金额
     */
    public void buy(){
        totalAmount += amount;
    /* 变化点，我们将策略的制定转移给了策略工厂，将这部分责任分离出去 */
        calPrice = CalPriceFactory.getInstance().createCalPrice(this);
    }


    /**
     * 计算客户最终要付的钱
     * @return
     */
    public Double calLastAmount(){
        return calPrice.calPrice(amount);
    }
}
