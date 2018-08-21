package com.example.demo.design.strategy;

/**
 * 超级玩家
 */
@PriceRegion(min=20000,max=30000)
public class SuperVip implements CalPrice{
    @Override
    public Double calPrice(Double orgnicPrice) {
        return orgnicPrice * 0.8;
    }
}
