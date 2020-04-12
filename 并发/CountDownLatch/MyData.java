public enum MyData {
    ONE(1, "齐"), TWO(2, "楚"), THREE(3, "燕"), FOUR(4, "赵"), FIVE(5, "魏"), SIX(6, "韩");
    private Integer code;
    private String Msg;

    MyData(Integer code, String msg) {
        this.code = code;
        this.Msg = msg;
    }
    public static MyData get(Integer code){
        MyData[] myDatas = MyData.values();
        for (MyData myData: myDatas) {
            if (myData.getCode() == code) {
                return myData;
            }
        }
        return null;
    }

    public Integer getCode() {
        return code;
    }

    public String getMsg() {
        return Msg;
    }
}
