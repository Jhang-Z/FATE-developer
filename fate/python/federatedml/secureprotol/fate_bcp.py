from charm.toolbox.integergroup import IntegerGroup
from charm.schemes.pkenc.pkenc_rsa import RSA_Enc, RSA_Sig
from charm.core.math.integer import integer,randomBits,random,randomPrime,isPrime,encode,decode,hashInt,bitsize,legendre,gcd,lcm,serialize,deserialize,int2Bytes,toInt
from federatedml.secureprotol.fixedpoint import FixedPointNumber


class Param():
    def __init__(self):
        pass
    def setParam(self,N2,N,g,k):
        self.N2 = N2
        self.N = N
        self.g = g
        self.k = k
    def print_members(self):
        for key, value in self.__dict__.items():
            print(f"{key}: {value}")

# N2 = integer(24909175282491185900622471475734487006720715716486555336782072271614754466990361512721529299568749813868881292525909179261483910184417049388201509697171452028284805245603199692550650198590023902334877588173260588213204554922779545176007477394855078331978545316541981373131166341994379118046312932354573040153785637009988399346107305847554254370062730006371324910358950338600926135104594559498343854548413732104023305604315529161653644617643571067003663688304267564548103368319673919506594368570558926541030296668504456191962834753139361186533069096462690645227092906550641203334966468860273569037762584961002518939161)
# N = integer(157826408697946320280866448795225315625389093422464504612384926214076108431420011786948715633310360413724731709352595437795790444470458401888466445403925642111660080072994359792736077376955962137260873025325013315900261557449651476851339087781286814375072544440445776257104128282107120514119757834203776837381)
# g = integer(22305288678755188224695454232302975021316707082496588221563268151241405914160131984704042862155106195307819437117933690536606476642223621733518126185363214829444547556264534914690434726943882075409860966692355530326598290370823291573567272142463851016886354973080966661276203326474516117331445976781883039680736038607503533041934762510504437858433307938321308946394650291823468593913492787358911323507798852737506922030854774433708287410583133780668512217023969477585511289800892839999798671168866182907752927056817947797406130387754306579322416522547725522889529600988580210738909266882324280204785026596782250130213)%N2
# k = integer(114646099306183058320314371293687095167731792223466252496561237837048268497985313077770605536400406699709901353511451684346347885905306178061300081897511421609929265526887403303036263542430503077827690710266731508360072109844558880970341251079461095125399165773705664831864556810792327846470735306978995584974)%N
# param = Param()
# param.setParam(N2, N, g, k)
# ppp = int(6199231838813608560128825840943705611047835889611906415426341072897522356970459201317817683028216368114022555280274345587135295624429353335116688921348321)
# qqq = int(6364756666696574602773432692730021673907535198715517463011000849787693699407883726454354570962903598380384806945000575263398961366367251249778052673243083)


class BCP():
    # def __init__(self,secparam=1024,param = True):
    #     if param:
    #         self.N2 = N2
    #         self.N = N
    #         self.g = g
    #         self.k = k
    #         self.MK =  {'pp':ppp, 'qq': qqq}
    def __init__(self,secparam=1024,param = None):
        if param:
            param.N2 = integer(param.N2)
            param.N = integer(param.N)
            param.g = integer(param.g) % param.N2
            param.k = integer(param.k) % param.N
            self.N2 = param.N2
            self.N = param.N
            self.g = param.g
            self.k = param.k            
        else:
            self.p, self.q = randomPrime(int(secparam/2),True), randomPrime(int(secparam/2),True) 
            self.pp = (self.p -1)/2
            self.qq = (self.q - 1)/2
            self.N = self.p * self.q
            while True: 
                if bitsize(self.N) ==secparam and len(int2Bytes(self.N)) == int(secparam/8) and int2Bytes(self.N)[0] &128 !=0:
                    break
                self.p, self.q = randomPrime(int(secparam/2),True), randomPrime(int(secparam/2),True) 
                self.pp = (self.p -1)/2
                self.qq = (self.q - 1)/2
                self.N = self.p * self.q
            self.N2 = self.N**2
            self.g = random(self.N2)
            one = integer(1)% self.N2
            while True: #choose a good g
                self.g = random(self.N2)
                self.g = integer((int(self.g)-1)*(int(self.g)-1))% self.N2
                if self.g == one:
                    continue
                tmp = self.g**self.p %self.N2
                if tmp == one:
                    continue
                tmp = self.g**self.pp % self.N2
                if tmp == one:
                    continue
                tmp = self.g**self.q %self.N2
                if tmp == one:
                    continue
                tmp = self.g**self.qq %self.N2
                if tmp == one:
                    continue
                tmp =self.g**(self.p*self.pp) % self.N2
                if tmp == one:
                    continue 
                tmp = self.g**(self.p*self.q) %self. N2
                if tmp== one:
                    continue 
                tmp = self.g**(self.p*self.qq) % self.N2
                if tmp == one:
                    continue 
                tmp = self.g**(self.pp*self.q) % self.N2
                if tmp == one:
                    continue 
                tmp = self.g**(self.pp*self.qq) % self.N2
                if tmp == one:
                    continue 
                tmp = self.g**(self.q*self.qq) % self.N2
                if tmp == one:
                    continue
                tmp = self.g**(self.q*self.qq) % self.N2
                if tmp == one:
                    continue
                tmp = self.g**(self.p*self.pp*self.q) % self.N2
                if tmp == one:
                    continue   
                tmp =self.g**(self.p*self.pp*self.qq) % self.N2
                if tmp == one:
                    continue
                tmp =self.g**(self.p*self.q*self.qq) % self.N2
                if tmp == one:
                    continue
                tmp =self.g**(self.pp*self.q*self.qq) % self.N2
                if tmp == one:
                    continue  
                break 
            # self.k = integer(int(self.g**(self.pp*self.qq) - 1) / self.N) % self.N
            self.k = integer((int(self.g**(self.pp*self.qq)) - 1)) / self.N % self.N
            
            self.MK ={"pp":int(self.pp),"qq":int(self.qq)}
    
    def GetMK(self):
        return self.MK
    
    def GetParam(self):
        param = Param()
        param.setParam(int(self.N2), int(self.N), int(self.g), int(self.k))
        return param
    
    def KeyGen(self):
        tmp = self.N2 /2
        sk = random(tmp) % self.N2
        pk = (self.g**sk) % self.N2
        # 返回的是int、integer
        return int(pk),sk
    
    def Encrypt(self,pk,plaintext):
        # 格式转换
        pk = integer(pk) % self.N2
        
        r = random(self.N/4) % self.N2
        A = (self.g** r ) % self.N2 
        B1 = (self.N*plaintext+1)% (self.N2)
        B2 = (pk**r) % (self.N2)
        B = B1*B2 % self.N2
        # 格式转换
        A = int(A)
        B = int(B)
        
        ciphertext = {"A":A,"B":B}
        return ciphertext
    
    def Decrypt(self,ciphertext,sk):
        
        # 传入的字典值为int, 转化成integer(mod N2)
        # ciphertext['A'] = integer(ciphertext['A'])
        # ciphertext['B'] = integer(ciphertext['B'])
        
        ciphertext['A'] = integer(int( ciphertext['A']))% self.N2
        ciphertext['B'] = integer(int( ciphertext['B']))% self.N2
        
        t1 = integer(int(ciphertext['B']*((ciphertext['A']**-1)**sk)) -1) % self.N2
        m = integer(t1) / self.N
        return int(m)
    
    def DecryptMK(self,ciphertext,MK,pk):
        
        ciphertext['A'] = integer(int( ciphertext['A']))% self.N2
        ciphertext['B'] = integer(int( ciphertext['B']))% self.N2
        pk = integer(pk) % self.N2
        MK['pp'] = integer(MK['pp']) 
        MK['qq'] = integer(MK['qq'])
        
        k_1 = self.k ** -1
        tmp = (int(pk**(MK['pp']*MK['qq'])) -1) % self.N2
        tmp = integer(tmp) /self.N 
        a = tmp * integer(k_1) % self.N
        
        tmp = (int(ciphertext['A'] **(MK['pp']*MK['qq'])) -1) % self.N2
        tmp = integer(tmp) /self.N 
        r = tmp * integer(k_1) % self.N
        
        gama = a*r %self.N
        sig = ((MK['pp']*MK['qq'])%self.N) **-1
        
        tmp = (self.g **-1)**gama
        tmp = ciphertext['B'] *tmp    
        tmp = (int(tmp**(MK['pp']*MK['qq'])) -1)% self.N2
        tmp = integer(tmp) /self.N
        
        m = integer(tmp) * integer(sig) %self.N
        # return integer(m) 
        return int(m)

    def multiply(self,ciphertext1,ciphertext2):
        
        ciphertext1['A'] = integer(int( ciphertext1['A']))% self.N2
        ciphertext1['B'] = integer(int( ciphertext1['B']))% self.N2
        
        ciphertext2['A'] = integer(int( ciphertext2['A']))% self.N2
        ciphertext2['B'] = integer(int( ciphertext2['B']))% self.N2
        
        ciphertext={}
        ciphertext['A'] = ciphertext1['A'] * ciphertext2['A']
        ciphertext['B'] = ciphertext1['B'] * ciphertext2['B']
        
        ciphertext['A'] = int(ciphertext['A'])
        ciphertext['B'] = int(ciphertext['B'])
         
        return ciphertext

    
    def exponentiate(self,ciphertext,m):
        
        ciphertext['A'] = integer(int( ciphertext['A']))% self.N2
        ciphertext['B'] = integer(int( ciphertext['B']))% self.N2
        
        text={}    
        text['A'] = ciphertext['A'] **m % self.N2
        text['B'] = ciphertext['B'] **m % self.N2
        
        text['A'] = int(text['A'])
        text['B'] = int(text['B'])
        
        return text  

class BCPEncryptedNumber(object):
    """代表BCP加密的整数浮点数
    """
    def __init__(self, public_key, ciphertext, exponent=0):
        self.public_key = public_key
        self.ciphertext = ciphertext
        self.exponent = exponent

    def __mul__(self, scalar, N2):
        """return Multiply by an scalar(int)
        """
        if isinstance(scalar, FixedPointNumber):
            scalar = scalar.decode()
        encode = FixedPointNumber.encode(scalar)
        plaintext = encode.encoding

        if plaintext < 0 :
            raise ValueError("Scalar out of bounds: %i" % plaintext)

        #做乘法  也要有int integer转换
        ciphertext = {}
        ciphertext['A'] = integer(int( self.ciphertext['A']))% N2
        ciphertext['B'] = integer(int( self.ciphertext['B']))% N2
        text={}
            
        text['A'] = ciphertext['A'] **plaintext % N2
        text['B'] = ciphertext['B'] **plaintext % N2
        text['A'] = int(text['A'])
        text['B'] = int(text['B'])

        exponent = self.exponent + encode.exponent

        return BCPEncryptedNumber(self.public_key, text, exponent)

    def increase_exponent_to(self, new_exponent, N2):
        """return BCPEncryptedNumber:
           new BCPEncryptedNumber with same value but having great exponent.
        """
        if new_exponent < self.exponent:
            raise ValueError("New exponent %i should be great than old exponent %i" % (new_exponent, self.exponent))
        
        factor = pow(FixedPointNumber.BASE, new_exponent - self.exponent)
        new_encryptednumber = self.__mul__(factor, N2)
        new_encryptednumber.exponent = new_exponent

        return new_encryptednumber
    
    
    
    
    
    
if __name__ == "__main__":

    bcp = BCP()
    mk = bcp.GetMK()
    print("mk is:",mk)
    pk,sk = bcp.KeyGen()
    print("------------------------")
    print("pk is:",pk,"sk is:",sk)
    plaintext = 1024
    print("------------------------")
    print("plaintext is:",plaintext)
    ciphertext = bcp.Encrypt(pk,plaintext)
    print("-------------------------")
    print("ciphertext is:",ciphertext)
    m1 = bcp.Decrypt(ciphertext,sk)
    print("-------------------------")
    print("Using sk to decrypt ciphertext,result is:",m1)
    m2 = bcp.DecryptMK(ciphertext,mk,pk)
    print("-------------------------")
    print("Using mk to decrypt ciphertext,result is:",m2)