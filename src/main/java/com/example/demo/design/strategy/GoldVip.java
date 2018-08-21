package com.example.demo.design.strategy;

/**
 * 金牌玩家
 */
@PriceRegion(min=30000)
public class GoldVip implements CalPrice{
    @Override
    public Double calPrice(Double orgnicPrice) {
        return orgnicPrice * 0.7;
    }
}
