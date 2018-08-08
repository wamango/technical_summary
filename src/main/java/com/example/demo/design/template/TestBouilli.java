package com.example.demo.design.template;

public class TestBouilli {

    public static void main(String[] args) {
        DodishTemplate dodishTemplate = new EggsWithTomato();
        dodishTemplate.dodish();
        System.out.println("----------");

        dodishTemplate = new Bouilli();
        dodishTemplate.dodish();
    }
}
