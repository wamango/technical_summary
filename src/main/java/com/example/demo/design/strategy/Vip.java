package com.example.demo.design.strategy;

/**
 * vip玩家
 */
@PriceRegion(max = 20000)
public class Vip implements CalPrice {
    @Override
    public Double calPrice(Double orgnicPrice) {
        return orgnicPrice * 0.9;
    }
}
