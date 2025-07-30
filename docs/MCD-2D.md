## Parameter: MCD-2D V2.2 - 7.3.5.4

A response or a request consists of one or more parameters (`PARAM`s).

There are several types of parameters:
  - `VALUE`
  - `RESERVED`
  - `CODED-CONST`
  - `PHYS-CONST`
  - `LENGTH-KEY`
  - `MATCHING-REQUEST-PARAM`
  - `TABLE-KEY`
  - `TABLE-STRUCT`
  - `TABLE-ENTRY`
  - `DYNAMIC`
  - `SYSTEM`
  - `NRC-CONST`

All of them can be used directly or indirectly in a response and in a request,
except that `MATCHING-REQUEST-PARAM`, `DYNAMIC` and `NRC-CONST` may only be used in a response.

Matching of result parameters can be done in one of the following ways:
  - `MATCHING-REQUEST-PARAM` (repetition of data from request)
  - `CODED-CONST` (matching with fixed coded-value)
  - `NRC-CONST` (matching with one of the fixed coded-values)
  - `PHYS-CONST` (matching with fixed physical value)

`BYTE-POSITION` and `BIT-POSITION` specify the start position of the parameter in the PDU, where the counting starts with 0.
This information is used for extraction of the parameter from the response PDU.

Sometimes, the position of a parameter cannot be determined until runtime, so the `BYTE-POSITION` and the `BIT-POSITION` shall be omitted in the ODX instance.
The parameter starts then at the byte edge next to the end of the last parameter.
All unpositioned parameters are extracted in the order in which they are specified in ODX.

If the unpositioned parameters follows a `COMPLEX-DOP` (7.3.6), e.g. `STRUCTURE`, then it follows behind the total size of the `COMPLEX-DOP`
(e.g. given by the "longest" parameter in any order, or by `BYTE-SIZE`).

A `PARAM` which is referenced by another `PARAM` (e.g. `LENGTH-KEY` and `TABLE-KEY`) shall be specified before the referencing `PARAM` (in order of appearance in
the XML document) or shall be positioned.

`BIT-POSITION` shall not have a value greater than 7.

A dataobject of `DIAG-CODED-TYPE` **A_BYTEFIELD**, **A_ASCIISTRING**, **A_UTF8STRING**, and **A_UNICODE2STRING**, as well as complex dataobjects,
shall cover whole bytes, i.e. the `BIT-POSITION` shall be 0 and the `BIT-LENGTH` shall be a multiple of 8 (or 16, in the case of **A_UNICODE2STRING**).
This is valid even if the `BIT-LENGTH` of the dataobject is dynamically defined by `MIN-MAX-LENGTH` type, `LEADING-LENGTH-INFO`, or `PARAM-LENGTH-INFO-TYPE`.


## VALUE parameter: MCD-2D V2.2 - page 78, paragraph 1

A `VALUE` parameter is a frequently used parameter type.
It references a DOP, which converts a concrete value from coded into physical representation and vice versa.

In a response message, `PHYSICAL-DEFAULT-VALUE` is used for verification of the received value.
In this case, the received coded value shall be converted into the physical representation.
After that, the specified and the received values can be compared.


## RESERVED parameter: MCD-2D V2.2 - page 78, paragraph 2

A parameter of type `RESERVED` is used when the parameter should be ignored
by the D-server.

Such parameters are not interpreted and are not shown on the user's display.

If the last or the first parameter of the PDU should not be interpreted,
it shall not be omitted. It shall be defined in the ODX instance as `RESERVED`,
in order to compute the PDU length and to compare it with the length
of the received PDU in case of a response.

Every bit in a request covered by a `RESERVED` parameter shall be filled with 0.


## CODED-CONST parameter: MCD-2D V2.2 - page 79, paragraph 1

`CODED-CONST` parameters can be used in a response for verification of the received value
(e.g. a service identifier, which is always constant) without converting it into the physical representation.

If a physical value is required for this parameter, a `COMPU-METHOD` of type `IDENTICAL` is assumed (see 7.3.6.6.2).


## PHYS-CONST parameter: MCD-2D V2.2 - page 79, paragraph 2

`PHYS-CONST` is an alternative for `CODED-CONST` with the difference that the value is given in the physical representation.

In a response, the received coded value shall be converted into the physical representation.
After that, the specified and the calculated values can be compared.


## Data Parameter: MCD-2D V2.2 - 7.3.6

The following classes of diagnostic data objects are used for request and/or response parameters:
  - `DATA-OBJECT-PROP` (*SimpleData*): represents a single value, consists of data types for coded and physical format, constraints, computation methods, and references physical units
  - `DTC-DOP` (*SimpleData*): represents a single diagnostic trouble code (DTC), consists of data types for coded and physical format, computation methods, and collection of possible DTC values
  - `STRUCTURE` (*ComplexData*): container for data parameters of any class
  - `MUX` (*ComplexData*): multiplexed data parameters
  - `ENV-DATA` (*ComplexData*): container for environment data parameters belonging to one DTC
  - `ENV-DATA-DESC` (*ComplexData*): multiplexed environment data parameters data belonging to DTC information
  - `FIELD` (`STATIC-FIELD`, `DYNAMIC-ENDMARKER-FIELD`, `DYNAMIC-LENGTH-FIELD`, `END-OF-PDU-FIELD`) (*ComplexData*): container for data parameters that are repeated within the PDU
  - `TABLE`: multiplexed data parameters with table structure


---


## SIMPLE DATA - DATA-OBJECT-PROP: MCD-2D V2.2 - 7.3.6.2

The class `DATA-OBJECT-PROP` describes how to extract and decode a single
data item from the byte stream of the response message and how to transform
the internal value into its physical representation using a computational method
(`COMPU-METHOD`).

After the conversion, a `UNIT-REF` can be used to reference a `UNIT` in order to provide
additional visualization information for the value.

A `DATA-OBJECT-PROP` is identified by its `SHORT-NAME` and `ID`.

It consists of a `COMPU-METHOD`, a `DIAG-CODED-TYPE` and a `PHYSICAL-TYPE`.

The implicit valid range of a data type is defined by `BASE-DATA-TYPE`, restricted by
`ENCODING` and size of the parameter, which is defined either by the number of 1 in a
condensed `BIT-MASK` or by the `BIT-LENGTH`.

Optionally, an `INTERNAL-CONSTR` and a `PHYS-CONSTR` can be given for a `DATA-OBJECT-PROP`,
and a `UNIT` may be referenced.
The explicit valid range is defined by `UPPER-LIMIT` and `LOWER-LIMIT`,
minus all `SCALE-CONSTR` with `VALIDITY != VALID`.
If the `UPPER-LIMIT` or the `LOWER-LIMIT` is missing, the explicit valid range
is not restricted in that direction.
The valid range is defined by the intersection of the implicit and the explicit
valid range.
`SCALE-CONSTR`s are not allowed to overlap each other, and shall be defined within
`INTERNAL-CONSTR` limits.

`DIAG-CODED-TYPE` is responsible for extraction of the coded value out of the byte
stream.

The coded value type inside the message is described by the member `BASE-DATA-TYPE`
of the `DIAG-CODED-TYPE`.

The extracted and decoded data item is stored within the D-server as an
internal value. The internal value type is connected with the coded value type.

Because the decoded value of type **A_ASCIISTRING** cannot be stored as an ASCII string
(the character set becomes larger during decoding), the internal value type of
any string type is **A_UNICODE2STRING** (see 7.3.6.6.2 and 7.3.6.6.9).

Predefined ODX base data types:

|  BASE-DATA-TYPE  |                                         Description                                                    |
|:----------------:|:------------------------------------------------------------------------------------------------------:|
| A_INT32          | 32 bit signed integer (range: -2<sup>31</sup> .. 2<sup>31</sup>-1)                                     |
| A_UINT32         | 32 bit unsigned integer (range: 0 .. 2<sup>32</sup>-1)                                                 |
| A_FLOAT32        | 32 bit float (IEEE754 single precision)                                                                |
| A_FLOAT64        | 64 bit float (IEEE754 double precision)                                                                |
| A_ASCIISTRING    | ISO-LATIN-1 (ISO/IEC 8859-1) coded character field with maximum length: 2<sup>31</sup>-1 bytes         |
| A_UTF8STRING     | UTF-8 coded character field with maximum length: 2<sup>31</sup>-1 bytes                                |
| A_UNICODE2STRING | UNICODE-2 (ISO/IEC 10646 UCS-2) coded character field with maximum length: 2<sup>31</sup>-1 characters |
| A_BYTEFIELD      | Byte field with maximum length: 2<sup>32</sup>-1                                                       |

The internal value and its type are used as input for the computational method
(`COMPU-METHOD`) to transform the value into its physical representation (physical value).

Consequentially, the `COMPU-METHOD` within a DOP shall support the internal and physical
value type of it.

The detailed description of `COMPU-METHOD`s occurs in section 7.3.6.6.

There are four types of the class `DIAG-CODED-TYPE`:
  - `LEADING-LENGTH-INFO-TYPE`:
      The length of the parameter is to be extracted from the PDU.
      
      `BIT-LENGTH` specifies the bit count at the beginning of this parameter and
      shall be greater than 0.
      These bits contain the length of the parameter in bytes.
      
      The bits of length information are not part of the coded value.
      That means the data extraction of the coded value starts at the byte edge
      to this length information.
      
      The attribute `IS-HIGHLOW-BYTE-ORDER` of the `DIAG-CODED-TYPE` is applied to the
      extraction of the coded value (except **A_BYTEFIELD**, **A_ASCIISTRING**, and
      **A_UTF8STRING**) and the leading length parameter.
  
  - `PARAM-LENGTH-INFO-TYPE`:
      The length of the parameter is defined by another parameter referenced
      by this kind of `DIAG-CODED-TYPE`.
      
      The physical value of the referenced parameter defines the length of
      the referencing parameter in bits.
  
  - `MIN-MAX-LENGTH-TYPE`:
      The minimum and the maximum length of a parameter in a message are
      specified by `MIN-LENGTH` and `MAX-LENGTH`.
      
      Both values (`MIN-LENGTH` and `MAX-LENGTH`) are to be given in number of bytes.
      By consequence, the coded parameter shall at minimum have the length
      of `MIN-LENGTH` and at maximum the length of `MAX-LENGTH` bytes, independent
      of `TERMINATION`.
      
      `TERMINATION` specifies a possible premature end of a parameter in the message,
      that is, the end of the parameter is reached before `MAX-LENGTH` bytes have been
      read.
      
      The following values for `TERMINATION` are possible:
      - `ZERO`:
          The byte stream to be extracted is terminated by the first of the following
          conditions:
          - finding termination character 0x00 (**A_ASCIISTRING** and **A_UTF8STRING**)
            or 0x0000 (**A_UNICODE2STRING**) after `MIN-LENGTH` bytes
          - reaching `MAX-LENGTH` bytes
          - reaching end of PDU
      - `HEX-FF`:
          The byte stream to be extracted is terminated by the first of the following
          conditions:
          - finding termination character 0xFF (**A_ASCIISTRING** and **A_UTF8STRING**)
            or 0xFFFF (**A_UNICODE2STRING**) after `MIN-LENGTH` bytes.
          - reaching `MAX-LENGTH` bytes
          - reaching end of PDU
      - `END-OF-PDU`:
          The byte stream to be extracted is terminated by the first of the following
          conditions:
          - reaching `MAX-LENGTH` bytes
          - reaching end of PDU
      - If the end of the PDU is reached before `MIN-LENGTH` bytes have been read,
        an error has to be returned at runtime.

      If the actual payload of the parameter is shorter than `MAX-LENGTH`, the
      termination value has to be coded into the PDU in case of `TERMINATION`
      equal to `ZERO` or `HEX-FF`.
      
      If the actual payload length of the parameter is equal to the `MAX-LENGTH`,
      the termination value is omitted (it is not coded into the request, and
      the coded value of the corresponding response parameter does not contain
      the termination byte). Only the payload will be encoded and converted.
      
      The termination value is not used for conversion, but it is considered
      if the next parameter has an undefined `BYTE-POSITION`, i.e. the next
      parameter follows the termination value.
      
      In the case of **A_UNICODE2STRING**, it is necessary to test the termination
      value 0x0000 and 0xFFFF as character codes, rather the sequence of 2 bytes
      with values 0x00 or 0xFF.
      - For example, the unicode string "Āa" has the byte sequence 0x01 0x00 0x00 0x61
        assuming a byteorder `HIGH-LOW`.
        Both values 0x00 in the middle may not be nterpreted as a `ZERO` termination.
      
      The termination characters 0xFF and 0xFFFF are not valid UTF-8 and UCS-2 characters,
      respectively. Therefore, they are suitable as termination characters.
      
      In the case of **A_UNICODE2STRING**, the length of the actual payload and the values
      of `MIN-LENGTH` and `MAX-LENGTH` shall be even. Otherwise, the D-server has to report an error.
  
  - STANDARD-LENGTH-TYPE:
      The parameter always occupies the specified length of `BIT-LENGTH` bits
      inside the message.
      
      If a provided value is shorter than the specified length, an error
      has to be signaled.
      
      The value of `BIT-LENGTH` shall be greater than 0.
      
      Optionally, an attribute `BIT-MASK` can be specified, if not all
      `BIT-LENGTH` bits inside the request message should be modified
      by the parameter value, or some bits inside the response message
      should be masked out.
      
      The length of the bit mask shall be equal to the `BIT-LENGTH`.
      
      If the parameter does not occupy a continuous bit stream inside the message,
      the optional attribute `CONDENSED = true` can be combined with `BIT-MASK`.
      In this case, the unset bits inside the bit mask do not only specify
      the unaffected bits inside the message, but additionally the bits
      to remove from the coded value while the extraction step by shifting
      the higher bits to the lower bits.

`LEADING-LENGTH-INFO-TYPE` and `MIN-MAX-LENGTH-TYPE` are only allowed for the internal data types
**A_BYTEFIELD**, **A_ASCIISTRING**, **A_UNICODE2STRING** and **A_UTF8STRING**.

Regardless of the type of length specification, the following additional
restrictions have to be considered depending on the `BASE-DATA-TYPE`:
  - **A_INT32** and **A_UINT32**: length shall be between 1 bit and 32 bits
  - **A_FLOAT32**: length shall be exactly 32 bits
  - **A_FLOAT64**: length shall be exactly 64 bits
  - **A_BYTEFIELD**, **A_ASCIISTRING**, and **A_UTF8STRING**: length shall be a multiple of
    8 bits (i.e. whole bytes)
  - **A_UNICODE2STRING**: length shall be a multiple of 16 bits (i.e. whole words)

The D-server has to report an error in the case of the violation of these restrictions.

The member `ENCODING` of the `DIAG-CODED-TYPE` gives the method used for encoding of
the value in the PDU:

|  BASE-DATA-TYPE  |                              Possible BASE-TYPE-ENCODINGs                              |
|:----------------:|:--------------------------------------------------------------------------------------:|
| A_INT32          | SM (sign-magnitude), 1C (one’s complement), 2C (two’s complement) (= default encoding) |
| A_UINT32         | BCD-P (packed BCD), BCD-UP (unpacked BCD), NONE (= default encoding)                   |
| A_FLOAT32        | IEEE754 (= default encoding)                                                           |
| A_FLOAT64        | IEEE754 (= default encoding)                                                           |
| A_ASCIISTRING    | ISO-8859-1 (= default coding), ISO-8859-2, WINDOWS-1252                                |
| A_UTF8STRING     | UTF-8 (= default encoding)                                                             |
| A_UNICODE2STRING | UCS-2 (= default encoding)                                                             |
| A_BYTEFIELD      | BCD-P (packed BCD), BCD-UP (unpacked BCD), NONE (= default encoding)                   |

Description of the `BASE-TYPE-ENCODING` enumeration:

| Value | Description |
|:-:|:--|
| BCD-P        | Packed BCD format<br>A BCD digit is packed in 4 bits (nibble) (47 = 0x47). |
| BCD-UP       | Unpacked BCD format<br>A BCD digit is mapped to one byte (17 = 0x0107). |
| 1C           | One’s complement |
| 2C           | Two’s complement |
| SM           | Sign-Magnitude<br>The encoding sign-magnitude means the first bit represents the sign (e.g. "1" equals "-"). In the following bits, the magnitude of the value is coded. 
| UTF-8        | UTF-8 Encoding Form: The Unicode encoding form which assigns each Unicode scalar value to an unsigned byte sequence of one to four bytes in length.<br>UTF-8 Encoding Scheme: The Unicode encoding scheme that serializes a UTF-8 code unit sequence in exactly the same order as the code unit sequence itself. |
| UCS-2        | ISO/IEC 10646 encoding form: Universal Character Set coded in 2 octets. |
| ISO-8859-1   | ISO/IEC 8859-1: Latin alphabet No. 1 |
| ISO-8859-2   | ISO/IEC 8859-2: Latin alphabet No. 2 |
| WINDOWS-1252 | Windows Code Page 1252 (Latin 1) |
| NONE         | In case the BASE-TYPE-ENCODING is not defined explicitly, the "default encoding" has to be applied. |

If the D-server is not able to encode or decode the value according to the `ENCODING`
specified, it has to provide an appropriate error message.

> [!NOTE]
> Binary-coded decimal encoding of `BASE-DATA-TYPE` = **A_BYTEFIELD**:
> 
> Binary-coded decimal (BCD) is an encoding for decimal numbers, in which
> each digit is represented by its own binary sequence.
> 
> Its main virtue is that it allows easy conversion to decimal digits for printing
> or display, and faster decimal calculations.
> 
> In case of a `BCD` encoded **BYTEFIELD** in the PDU, the D-server does not need
> to convert the coded into the internal value, it only has to check whether
> the value contains forbidden digits like 0xA to 0xF or not.
> 
> If a forbidden digit is used, the D-server has to provide an appropriate
> error message.
> 
> In a common use case, there will be no further calculation from the internal
> into the physical value, the byte sequence can be passed as identical value
> directly to the application.
> 
> Contrary to data types **A_UINT32** or **A_INT32** it is possible to cover values
> of more than 4 byte with data type **A_BYTEFIELD**.

`PHYSICAL-TYPE` specifies the physical representation of the value.

The member `BASE-DATA-TYPE` gives the type and encoding of the physical value again.

Physical values always have the default encoding of their respective type,
as defined in the table above.

The optional member `DISPLAY-RADIX` is used for visualization purposes,
i.e. it specifies whether the physical value is to be displayed in a hexadecimal,
decimal, binary or octal representation. The corresponding attribute values are
`HEX`, `DEC`, `BIN` or `OCT`. It is only applicable to the physical data type **A_UINT32**.

There is also a possibility to specify the number of digits to be displayed
after the decimal point by the member `PRECISION`. It can be given for
**A_FLOAT32** and **A_FLOAT64** data types and is used for the visualisation of the
physical value at the tester side.
  - For example, to display the value *1.234*, the `PRECISION` is to be set
    to 3, while *0.00010* requires a `PRECISION` of 5.

The calculated physical value can be directly displayed on the tester.

Usually, units are used to augment this displayed value with additional
information, like *m/s* or *liter*. Also, the conversion of values from one unit to another, like from *km/h* to *m/s*,
is possible. The declaration of the unit to be used is given via the reference
`UNIT-REF`. See 7.3.6.7 for more information about units.

The validity of the internal value can be restricted to a given interval
via the `INTERNAL-CONSTR` and its members `LOWER-LIMIT` and `UPPER-LIMIT`.

Additionally, `SCALE-CONSTRS` can be used to define valid, non-valid,
non-defined or non-available sub-intervals within the interval
spanned by `INTERNAL-CONSTR`.
The limits of the sub-intervals are defined with `LOWER-LIMIT` and `UPPER-LIMIT`
in the same way as in `INTERNAL-CONSTR`.

The attribute `VALIDITY` of each `SCALE-CONSTR` can take the values `VALID`,
`NOT-VALID`, `NOT-DEFINED` or `NOT-AVAILABLE`, respectively:

| VALIDITY | Description |
|:-:|:--|
| VALID         | Valid area.<br>Current value is within a valid range and can be presented to user. |
| NOT-VALID     | Invalid area.<br>The ECU cannot process the requested data. |
| NOT-DEFINED   | Indicates an area which is marked in a specification (e.g. as reserved).<br>Shall usually not be set by the ECU but is used by a tester to verify correct ECU behaviour.<br>Also prevents use of areas during editing process. |
| NOT-AVAILABLE | Currently invalid area.<br>The value usually is presented by the ECU but can currently not be performed due to e.g. initialisation or temporary problems.<br>This behaviour appears during runtime and cannot be handled while data is edited. |

The following restrictions regarding `SCALE-CONSTR` apply:
  - Each range of `SCALE-CONSTR` shall not overlap any other range.
    Two closed range ends with the same limit are prohibited.
  - Each range of `SCALE-CONSTR` shall fit into the `INTERNAL-CONSTR` range.
  - `LOWER-LIMIT/CONTENT` shall be less or equal to `UPPER-LIMIT/CONTENT`.
    If the `CONTENT` values are equal, the `INTERVAL-TYPE` of both shall be set to `CLOSED`.

Perhaps some information like "value is not valid" is not always sufficient.
Therefore, the `SHORT-LABEL` can be used to provide further information like
error messages.

The attribute `INTERVAL-TYPE` of `LOWER-LIMIT` and `UPPER-LIMIT` defines the type of the
interval at the corresponding end.
Possible values are `OPEN` (if the edge value is not to be included),
`CLOSED` (if it is to be included), or `INFINITE` (if the value defined by
`LOWER-LIMIT` is -∞ or if it is +∞ in the case of `UPPER-LIMIT`).

The value specified by the limit is ignored if `INTERVAL-TYPE = INFINITE`.

In case of no limit given, the interval is not constrained in that direction,
i.e. the limit is implicitly set to -∞ if `LOWER-LIMIT` is missing,
or to +∞ if no `UPPER-LIMIT` is given.

> [!IMPORTANT]
> The `LOWER-LIMIT` and `UPPER-LIMIT` of `INTERNAL-CONSTR` define the valid
> interval of values.
> 
> All values outside of this interval are not valid and thus are not to be
> processed by the ECU.
> 
> Therefore, the declaration of an `INTERNAL-CONSTR` is equivalent to the declaration
> of a `SCALE-CONSTR` with `VALIDITY = VALID`.
> 
> If neither `LOWER-LIMIT` nor `UPPER-LIMIT` is defined in `INTERNAL-CONSTR` directly,
> at least one `SCALE-CONSTR` with `VALIDITY` other than `VALID` shall exist.

The implicit valid range of a data type is defined by `BASE-DATA-TYPE`, restricted by
`ENCODING` and size of parameter which is defined either by the number of 1 in a
condensed `BIT-MASK` or the `BIT-LENGTH`.

The explicit valid range is defined by `UPPER-LIMIT` and `LOWER-LIMIT`, minus all
`SCALE-CONSTR`s with `VALIDITY != VALID`.

If `UPPER-LIMIT` or `LOWER-LIMIT` is missing, the explicit valid range is
not restricted in that direction.

The valid range is defined by the intersection of the implicit and the explicit
valid range.

`INTERNAL-CONSTR` can only be used in conjunction with a `DATA-OBJECT-PROP`,
which must have a numerical type of the internal value.

If the `DATA-OBJECT-PROP` is used for calculation of physical value from the internal one,
the internal value is matched against the valid range directly:
  1. Match internal value against the valid range defined above the `DATA-OBJECT-PROP`.
  
  2. If match was successful, i.e. the internal value is valid, then calculate
     the physical value from the internal value with the `COMPU-METHOD` of
     the `DATA-OBJECT-PROP`.
     
     If the value is outside the valid range, the D-server reports an error message.
     
     If the value falls into an explicitly specified invalid scale, the information
     of this `SCALE-CONSTR` is used to generate the error message.

If the `DATA-OBJECT-PROP` is used to transform the physical into the internal value,
the physical value given by the user is first converted into the internal
representation, and is then matched against the valid range:
  1. Calculate the internal value from the physical value with the `COMPU-METHOD`
     of the `DATA-OBJECT-PROP`.
  
  2. Match calculated internal value against the valid range defined above
     the `DATA-OBJECT-PROP`.
     
     If the value is outside the valid range, the D-server does not accept
     the physical value as an input value and reports an error message.
     
     If the value falls into an explicitly specified invalid scale,
     the information of this `SCALE-CONSTR` is used to generate the error message.

In a similar way, it is possible to specify constraints for the physical value
inside `PHYS-CONSTR`, if the physical type of the `DATA-OBJECT-PROP` is a
numerical type.

In this case, the implicit valid range is not restricted by the size
or encoding of the data type, only by the general restriction given by
the `BASE-DATA-TYPE`.

If the `DATA-OBJECT-PROP` is used for calculation of physical value from
the internal one, the physical value is matched against the valid physical range
after applying the conversion method.

If the `DATA-OBJECT-PROP` is used to transform the physical into the internal value,
the physical value given by the user is first matched against the valid physical range.


## Computational methods: MCD-2D V2.2 - 7.3.6.6

Computational methods (`COMPU-METHOD`) are needed to calculate between the internal
type and the physical type of the diagnostic values.

An internal diagnostic value is, for example, the result of the extraction of a response parameter from the response message
received from the ECU.
To this internal diagnostic value, a computational method is applied, to get the physical value for representation.

On the other hand, a physical value given by the user is to be converted into internal value in order to be sent to an ECU.
This is also done by means of the `COMPU-METHOD`.

The extraction of data items from a response and the coding of data items into a request are made via `DIAG-CODED-TYPE`
that is described in sections 7.3.6.2, 7.3.6.3, and 7.3.6.4.

A `COMPU-METHOD` can specify a `COMPU-INTERNAL-TO-PHYS` and/or a `COMPU-PHYS-TO-INTERNAL` element,
which specifies the transformation of a coded value read
out of the PDU into a physical value of a type compliant to the `DOP-BASE` this `COMPU-METHOD` belongs to,
or a physical value into a coded value, respectively.

For invertible `COMPU-METHODS` (e.g. a `LINEAR` function), the inversion has to be performed
automatically by e.g. a D-server.

In case the `COMPU-INTERNAL-TO-PHYS` calculation is not invertible, the corresponding `COMPU-PHYS-TO-INTERNAL` element
can be used to define a deterministic inverse calculation.
The same holds true, if only a `COMPU-PHYS-TO-INTERNAL` has been defined at this is not invertible.
A `COMPU-INTERNAL-TO-PHYS` can be used to solve this situation.

A `COMPU-METHOD` of one of the categories `RAT-FUNC`, `SCALE-RAT-FUNC`, or `COMPUCODE` is never invertible,
and a separate element for the inverse direction has to be specified, if the inverse direction is required.

Be aware that the author is responsible for the consistency between the `COMPU-INTERNAL-TO-PHYS` and the
`COMPU-PHYS-TO-INTERNAL` calculation, if this consistency is expected.
There is no possibility for an ODX tool to check that the one is really a valid inversion of
the other one.

For an example on the use of `COMPU-INVERSE-VALUE` please refer to section 7.3.6.6.7, where a `TEXTTABLE` is specified.
Since multiple internal values are mapped onto the same string as physical value, there is no deterministic inversion.
However, for every `COMPU-SCALE` element, a `COMPU-INVERSE-VALUE` is specified.
- For example, the values **5 .. 9** map onto the string "ON".
  Since it is non-deterministic to which value "ON" should be mapped when converting from physical to internal value,
  `COMPU-INVERSE-VALUE` defines this deterministically to be the value 5.
In case both directions (`COMPU-PHYS-TO-INTERNAL` and `COMPU-INTERNAL-TO-PHYS`) are defined in one `COMPU-METHOD`,
both need to be used in case this `COMPU-METHOD` appears in a `REQUEST` and `RESPONSE`.

If only one direction is used, inversion takes place in the respective other direction, if the corresponding conversion is
invertible:

| COMPU-METHOD specifies...                              | calculation of response uses...             | calculation of request uses...              |
|:------------------------------------------------------:|:-------------------------------------------:|:-------------------------------------------:|
| only COMPU-INTERNAL-TO-PHYS                            | COMPU-INTERNAL-TO-PHYS                      | COMPU-INTERNAL-TO-PHYS in inverse direction |
| both COMPU-INTERNAL-TO-PHYS and COMPU-PHYS-TO-INTERNAL | COMPU-INTERNAL-TO-PHYS                      | COMPU-PHYS-TO-INTERNAL                      |
| only COMPU-PHYS-TO-INTERNAL                            | COMPU-PHYS-TO-INTERNAL in inverse direction | COMPU-PHYS-TO-INTERNAL                      |

There are eight different types of `COMPU-METHOD`s: `IDENTICAL`, `LINEAR`, `SCALE-LINEAR`, `TEXTTABLE`, `COMPUCODE`, `TAB-INTP`,
`RAT-FUNC` and `SCALE-RAT-FUNC`.

The mandatory member `CATEGORY` defines the type of the `COMPU-METHOD`.
A generic approach is used for the definition of functions.

The following mathematical function forms the basis of all functions (apart from `IDENTICAL`, `TEXTTABLE` and `COMPUCODE`):
```math
f(x) = \frac{V_{N0} + V_{N1} * x + V_{N2} * x^2 + ... + V_{Nn} * x^n}{V_{D0} + V_{D1} * x + V_{D2} * x^2 + ... + V_{Dm} * x^m}
```

For each interval, a numerator (`COMPU-NUMERATOR`) and a denominator (`COMPU-DENOMINATOR`) is defined.
Each of them defines a sequence of `V-values` representing a polynomial.
The first `V` is the coefficient for x<sup>0</sup>, the second `V` is the coefficient for x<sup>1</sup> and so on.

The domain of categories `TEXTTABLE`, `SCALE-LINEAR` and `SCALE-RAT-FUNC` can be divided into several intervals,
each specified by one `COMPU-SCALE`.

The domain of categories `LINEAR` and `RAT-FUNC` shall define exactly one `COMPU-SCALE`, which may only restrict
the single domain.

The categories `IDENTICAL` and `COMPUCODE` shall not define any `COMPU-SCALE` at all.

The category `TAB-INTP` shall specify at least two `COMPU-SCALE`s, but in this case, each `COMPU-SCALE` will define
only a singular value, not an interval.

A scale for a function is defined via `COMPU-SCALE`.

When applying intervals for scales, defined by `UPPER-LIMIT` and `LOWER-LIMIT`, the user has to guarantee that no intervals
will overlap.
  - Exception: Only for the `COMPU-METHOD` of type `TEXTTABLE`, overlapping is allowed.
  
Therefore, the attribute `INTERVAL-TYPE`, and its values `OPEN`, `CLOSED` or `INFINITE` can be used.
The value `OPEN` does not include the boundary, whereas the value `CLOSED` does.
`INFINITE` denotes an open-end interval.

For the categories `LINEAR` and `RAT-FUNC`, a missing `LOWER-LIMIT` or `UPPER-LIMIT` means that the domain
is not restricted in this corresponding direction.

For the categories `TEXTTABLE`, `SCALE-LINEAR`, and `SCALE-RAT-FUNC`, the `LOWER-LIMIT` shall be defined in any
`COMPU-SCALE` definition.
If no `UPPER-LIMIT` is defined, the `COMPU-SCALE` will be applied only for the value defined in `LOWER-LIMIT`.
In this case, `INTERVAL-TYPE` at `LOWER-LIMIT` shall be defined as `CLOSED`.

For the category `TAB-INTP`, `LOWER-LIMIT` contains the singular value and `UPPER-LIMIT` shall not be present.

The processing order of the scales of any category is the order of specification inside the ODX document:
The first matching scale closes the processing in the D-server.
This is even the case if the value falls into several scales of a `TEXTTABLE`.

Besides the `COMPU-SCALE`s, the categories `TEXTTABLE`, `SCALE-LINEAR`, and `SCALE-RAT-FUNC` may define
an optionally default scale, `COMPU-DEFAULT-VALUE`.

If the `COMPU-METHOD` is used in the inverse direction, and if the optional `COMPU-INVERSE-VALUE` is not present
inside `COMPU-DEFAULT-VALUE`, then the default scale is ignored.

The use of this optional element differs for both computational directions, if it is really applicable:
  1. In the case of computational direction `internal to physical value`, the physical value is only reported as the result
     if the internal value does not match any defined interval (wherever they can be defined).
  
  2. In the case of computational direction `physical to internal value`, the internal value is only reported as the result
     if the physical value given as input value does not match any defined interval (wherever they can be defined),
     and if it is equal to the physical value given inside the default scale.

If the value does not fall into any `COMPU-SCALE` and if the optional `COMPU-DEFAULT-VALUE` is not present
or not applicable, then the D-server has to indicate a runtime error.

The different processing of the default scale for both directions reflects the idea that an invalid input value,
e.g. invalid due to a spelling error in the case of a `TEXTTABLE`, should not be accepted in the case of a request parameter,
while any allowed response parameter could use the default scale if applicable.

For all `COMPU-METHOD`s, except those of categories `IDENTICAL`, `TEXTTABLE` and `COMPUCODE`,
the calculation type (float or integer) is deduced from the type of the internal and physical values.
It has a decisive influence on the precision of the calculation.

The type of the calculation is determined according to the following rules:
  1. If one of the types (physical or internal) is **A_FLOAT32** or **A_FLOAT64**, the calculation is of type **A_FLOAT64**.
  2. If both types are **A_UINT32**, the calculation is of type **A_UINT32**.
  3. In any other case, the calculation is of type **A_INT32**.

The type of the coefficients in `COMPU-NUMERATOR` is equal to the type of the calculation.
Also, the type of the coefficients in `COMPU-DENOMINATOR` is equal to the type of the calculation,
except for the categories `LINEAR` and `SCALE-LINEAR`, where the only coefficient is always of type **A_UINT32**.

The `COMPU-DENOMINATOR` shall be non-zero.

If the `COMPU-DENOMINATOR` is not specified, the numerical value 1 is assumed for the denominator,
i.e. no division is executed.

The type of the values of the other elements inside `COMPU-INTERNAL-TO-PHYS` and `COMPU-PHYS-TO-INTERNAL`
are summarized in the following table:

|                  Element                  | COMPU-INTERNAL-TO-PHYS | COMPU-PHYS-TO-INTERNAL |
|:-----------------------------------------:|:----------------------:|:----------------------:|
| LOWER-LIMIT                               | internal type          | physical type          |
| UPPER-LIMIT                               | internal type          | physical type          |
| COMPU-INVERSE-VALUE                       | internal type          | physical type          |
| COMPU-CONST                               | physical type          | internal type          |
| COMPU-DEFAULT-VALUE                       | physical type          | internal type          |
| COMPU-DEFAULT-VALUE / COMPU-INVERSE-VALUE | internal type          | physical type          |

> [!IMPORTANT]
> Not all elements are applicable for all categories of `COMPU-METHOD`.
> 
> Some of the elements have the sub-elements `V` and `VT`.
> 
> In all of theses cases, the sub-element `V` shall be used for numerical types, and `VT` for non-numerical types.

If an overflow or division by zero occurs during the calculation, the D-server has to report an error message.

If the calculation type is **A_FLOAT64** and a result type is either **A_INT32** or **A_UINT32**,
the commercial rounding is applied, i.e. 0.5 -> 1, 1.3 -> 1, 1.5 -> 2.

---

###### IDENTICAL

A `COMPU-METHOD` of category `IDENTICAL` just passes on the input value, so that the internal value
and the physical one are identical.

Mathematical function:
```math
f(x) = x, \ x \in \mathbb{R}
```

Certain data types:
  - Internal: all types
  - Physical: all types
  - (physical type = internal type)

For `COMPU-METHOD`s of this type, the data objects `COMPU-INTERNAL-TO-PHYS` and `COMPU-PHYS-TO-INTERNAL` are not allowed.

This is the simplest type of a `COMPU-METHOD`.

The value domain of an identical function includes all values of all types (including ASCII strings).
In this case, the only limitation is that the physical and the internal types shall be identical.

If the coded type (at `BASE-TYPE-ENCODING` at `DIAG-CODED-TYPE`) is **A_ASCIISTRING** or **A_UTF8STRING**,
then the conversion to/from the physical `BASE-DATA-TYPE` **A_UNICODE2STRING** shall be done implicitly,
during the decoding/encoding process.

---

###### LINEAR

A `COMPU-METHOD` of category `LINEAR` multiplies the internal value with a factor and adds an offset.
Optionally, the sum can be divided by a constant unsigned integer.

Exactly one `COMPU-SCALE` has to be defined. It contains `COMPU-RATIONAL-COEFFS`, within which `COMPU-NUMERATOR`
and `COMPU-DENOMINATOR` are declared.

The numerator should contain two values. The first one is the offset (V<sub>N0</sub>),
the second one is the factor (V<sub>N1</sub>).

If the denominator is present, it shall specify exactly one unsigned integer value.

The `LIMIT`s at `COMPU-SCALE` can be used to restrict the value domain.

Via this `COMPU-METHOD`, it is possible to create a function which returns a constant value
by setting V<sub>N1</sub> = 0. In this case, `COMPU-INVERSE-VALUE` has to be defined if the reverse calculation is required.

Mathematical function:
```math
f(x) = \frac{V_{N0} + V_{N1} * x}{V_{D0}}
```

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**
  - Physical: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**

---

###### SCALE-LINEAR

A `COMPU-METHOD` of type `SCALE-LINEAR` is similar to `LINEAR`, with the difference
that more than one interval can be defined as the domain of the function, and different
calculations can be applied to the intervals.

The boundaries of the intervals shall not overlap.

Condition for invertibility:
  - Adjacent `COMPU-SCALES` shall have the same values on their
    common boundaries *AND* the V<sub>N1</sub> of all intervals shall have the same sign or shall be 0.
  - If V<sub>N1</sub> = 0, then `COMPU-INVERSE-VALUE` shall be specified.

Mathematical function:
```math
f(x) =
\left\lbrace
\begin{array}{cl}
\frac{V_{N0}^1 + V_{N1}^1 * x}{V_{D0}^1} & ,\ x \in I_1 \\
... \\
\frac{V_{N0}^n + V_{N1}^n * x}{V_{D0}^n} & ,\ x \in I_n
\end{array}
\right.
, \ \text{where} \ I_1,...I_n \ \text{are arbitrary disjunctive intervals.}
```

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**
  - Physical: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**

---

###### RAT-FUNC

A `COMPU-METHOD` of type `RAT-FUNC` differs from the `LINEAR` function in the omission of the restrictions for `COMPU-NUMERATOR`s and `COMPU-DENOMINATOR`s.
They can have as many `V`-values as needed.

The calculation in the reverse direction is not allowed for this type.

Mathematical function:
```math
f(x) = \frac{V_{N0} + V_{N1} * x + V_{N2} * x^2 + ... + V_{Nn} * x^n}{V_{D0} + V_{D1} * x + V_{D2} * x^2 + ... + V_{Dm} * x^m}
```

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**
  - Physical: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**

---

###### SCALE-RAT-FUNC

A `COMPU-METHOD` of type `SCALE-RAT-FUNC` can have more than one `COMPU-SCALE` to provide different calculations for different intervals.

The calculation in the reverse direction is not allowed for this type.

Mathematical function:
```math
f(x) =
\left\lbrace
\begin{array}{cl}
\frac{V_{N0}^1 + V_{N1}^1 * x + V_{N2}^1 * x^2 + ... + V_{Nn}^1 * x^n}{V_{D0}^1 + V_{D1}^1 * x + V_{D2}^1 * x^2 + ... + V_{Dm}^1 * x^m} & ,\ x \in I_1 \\
... \\
\frac{V_{N0}^k + V_{N1}^k * x + V_{N2}^k * x^2 + ... + V_{Nn}^k * x^n}{V_{D0}^k + V_{D1}^k * x + V_{D2}^k * x^2 + ... + V_{Dm}^k * x^m} & ,\ x \in I_k
\end{array}
\right.
, \ \text{where} \ I_1,...I_k \ \text{are arbitrary disjunctive intervals.}
```

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**
  - Physical: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**

---

###### TEXTTABLE

A `COMPU-METHOD` of category `TEXTTABLE` is used for transformations of the internal value into a textual expression.
It is commonly specified only by `COMPU-METHOD/COMPU-INTERNAL-TO-PHYS` and used in both directions.

At least one `COMPU-SCALE` shall be specified in `COMPU-METHOD/COMPU-INTERNAL-TO-PHYS`.
In each scale, `COMPU-SCALE/UPPER-LIMIT` and `COMPU-SCALE/LOWER-LIMIT` define an interval.
These scales may overlap.

To find a single matching interval, the `COMPU-SCALE`s are to be processed in ODX document order.
The first matching interval is taken.

`COMPU-SCALE/COMPU-CONST` with the data object `VT` defines the resulting text for the appropriate interval.

The optional `COMPU-METHOD/COMPU-INTERNAL-TO-PHYS/COMPU-DEFAULT-VALUE` can be used to define the physical value
if the internal value does not lie in any given interval.

If the internal data type is a string type, the definition of a range is not allowed.
If the element `UPPER-LIMIT` is explicitly specified, its content shall be equal to the content of `LOWER-LIMIT`.

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**, **A_ASCIISTRING**, **A_UTF8STRING**, **A_BYTEFIELD**,
    **A_UNICODE2STRING**
  - Physical: **A_UNICODE2STRING**

---

###### TAB-INTP

A `COMPU-METHOD` of category `TAB-INTP` defines a set of points with linear interploaton between them.

Only `LOWER-LIMIT` and `COMPU-CONST/V` are used for that purpose (`UPPER-LIMIT` should be omitted or shall be equal to `LOWER-LIMIT`).

If the calculation is used in the direction of specification, it is performed as follows:
  - The input value is matched against the value intervals in the order they are defined by the `COMPU-SCALE`s; the limits of a value interval
    are defined by the `LOWER-LIMIT` values of two adjacent `COMPU-SCALE`s.
  - The processing starts with the first and second `COMPU-SCALE`s; in the next step, the second and the third `COMPU-SCALE`s are checked;
    then the third and forth, and so on.
  - Once the input value matches an end point or lies inside an interval, the iteration is stopped and the result value is to be calculated
    via linear interpolation for the interval specified by the values inside `COMPU-CONST/V` of those two matched `COMPU-SCALE`s.
  - If the internal value is less than the smallest defined `LOWER-LIMIT` or greater than the greatest `LOWER-LIMIT`, a runtime error shall be indicated by the D-server.

The calculation in the reverse direction is performed in an analogous manner and also in the same order, with the difference that the input value is tested against the value
intervals, which are defined by the `COMPU-CONST/V` values of two adjacent `COMPU-SCALE`s.
The first pair of `COMPU-SCALE`s matching the value will be used to calculate the result in reverse direction by interpolation the interval specified by their `LOWER-LIMIT`s.

> [!NOTE]
> Example:
> 
> `COMPU-SCALE`#0: `LOWER-LIMIT` = 0, `COMPU-CONST/V` = 0\
> `COMPU-SCALE`#1: `LOWER-LIMIT` = 2, `COMPU-CONST/V` = 5\
> `COMPU-SCALE`#2: `LOWER-LIMIT` = 4, `COMPU-CONST/V` = 8\
> ...
> 
> If the coded value is between [0, 2], the physical value is interpolated between [0, 5].\
> If the coded value is between [2, 4], the physical value is interpolated between [5, 8].\
> ...

Possible data types:
  - Internal: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**
  - Physical: **A_INT32**, **A_UINT32**, **A_FLOAT32**, **A_FLOAT64**


## Complex DOPs - Overview: MCD-2D V2.2 - 7.3.6.10.1

Complex diagnostic data object properties (`COMPLEX-DOP`s) are used to define and interpret complex ECU responses
(or structured parts of a tester request) containing multiple data items, which are grouped in a structure or repeated in a field.
Additionally, there is a multiplexer, which is used to interpret alternative data depending on a switch-key.

They are needed to describe ECU responses which are dynamic, i.e. the size and actual structures that are known only at runtime.

Like the `simple DOP`s, `COMPLEX-DOP`s have the standard elements `SHORT-NAME`, `LONG-NAME`, `DESC`, `ID`, `SDGS`, and `ADMIN-DATA`.

`COMPLEX-DOP`s are referenced from a `PARAM` of a response in the same way like `simple DOP`s.

In contrast to `simple DOP`s, `COMPLEX-DOP`s usually contain further `PARAM`s (directly or indirectly), which can also refer to a further `COMPLEX-DOP`.

Because infinite recursion (e.g. by self-referencing) is forbidden, every branch shall terminate in a `PARAM` leaf which references `DATA-OBJECT-PROP` or `DTC-DOP`.

The `BYTE-POSITION`s and `BIT-POSITION`s of a `PARAM` are given there as absolute positions in the PDU if the `PARAM` is directly part
of a `POS-RESPONSE`, `NEG-RESPONSE`, `GLOBAL-NEG-RESPONSE` or `REQUEST`.

In contrast to that, the `BYTE-POSITION` of a `PARAM` used inside a `COMPLEX-DOP` is always given relatively to the start of this `COMPLEX-DOP`.

The `COMPLEX-DOP` itself shall start at a byte edge, i.e. the `BIT-POSITION` of the referencing parameter shall be 0 or absent.

Most classes derived from `COMPLEX-DOP` are allowed to be used only inside a response description.
Only `STRUCTURE` and `END-OF-PDU-FIELD` are usable directly or indirectly inside a `REQUEST`.


## Structure: MCD-2D V2.2 - 7.3.6.10.2

A `STRUCTURE` is some kind of wrapper to enable recursion, that combines
several `PARAM`s into a group of parameters belonging together.

Beside information structuring, the use of `STRUCTURE`s enables an easy reuse
of parameter groups.

The `BIT-POSITION` of a `PARAM` using a `STRUCTURE`, directly or via any kind
of `COMPLEX-DOP`, shall be absent or equal to 0, i.e. a `STRUCTURE` starts
always at byte edge.

In general, one or more `PARAM`s are defined inside a `STRUCTURE` in the same way
as within a response.
Each `PARAM` represents an item which is a member of the
group built by this `STRUCTURE`.

The optional attribute `BYTE-SIZE` gives the size of the whole structure in bytes.
It shall not be less than the total size of the included parameters.
It can be greater than the total size of the included items if the developer
aims to create space after the last item.

If the `STRUCTURE` has any dynamic components (e.g. `MUX`, or any `FIELD` with dynamic
length), the `BYTE-SIZE` should not be given.

Since a `COMPLEX-DOP` can contain `PARAM`s, which themselves can use `COMPLEX-DOP`s, it
is possible to define complex data structures recursively.


## Static field: MCD-2D V2.2 - 7.3.6.10.3

`STATIC-FIELD`s are used when the PDU contains a recurring structure and the number of repetitions is fixed and does not have to be determined dynamically.

In other words, a `STATIC-FIELD` is used to describe a repetition of a `BASIC-STRUCTURE` or `ENV-DATA-DESC` with an "a priori" fixed number of repetitions.

The meaning of the reference to `ENV-DATA-DESC` is that the actually selected `ENV-DATA` out of the `ENV-DATA`s, the `ENV-DATA-DESC` references to is taken for the repetitions.

The number of repetitions is given via the attribute `FIXED-NUMBER-OF-ITEMS`.

The reference to the `BASIC-STRUCTURE` or `ENV-DATA-DESC` defines the complex DOP to be repeatedly applied.

The first item starts at the same byte position as the `STATIC-FIELD`.

For each further item, the byte position is increased by `ITEM-BYTE-SIZE`, which determines the length of one item in the field.
It is given in bytes, and shall not be less than the length occupied by the `PARAM`s included by the repeated complex DOP,
or than the optional `BYTE-SIZE` of the `BASIC-STRUCTURE` referenced to.

> [!IMPORTANT]
> It shall be ensured that the items shall not exceed this fixed byte length, even if they contain dynamic data objects.


## Dynamic length field: MCD-2D V2.2 - 7.3.6.10.4

`DYNAMIC-LENGTH-FIELD`s are fields of items (`BASIC-STRUCTURE` or `ENV-DATA-DESC`)
with variable number of repetitions, which can be determined only at runtime.

The determination of the number of repetitions is described by `DETERMINE-NUMBER-OF-ITEMS`.

The `DATA-OBJECT-PROP` referenced to is used to calculate the repetition number,
which is contained in its physical value of type **A_UINT32**. Its `BYTE-POSITION` is
relative to that of the `DYNAMIC-LENGTH-FIELD`. The optional `BIT-POSITION` shall be
between 0 and 7.

The reference to the `BASIC-STRUCTURE` or `ENV-DATA-DESC` defines the `COMPLEX-DOP` to be
repeatedly applied.

For the first item, the byte position is given by `OFFSET` relatively to the
byte position of the `DYNAMIC-LENGTH-FIELD`.

Each further item starts at the byte edge following the item before (similar to
`PARAM`s without explicitly specified `BYTE-POSITION`).


## Dynamic Endmarker Field: MCD-2D V2.2 - 7.3.6.10.5

`DYNAMIC-ENDMARKER-FIELD`s are fields of items (`BASIC-STRUCTURE`s or `ENV-DATA-DESC`s) which are repeated until an end-marker is found (the `TERMINATION-VALUE`).
It is also terminated by the end of the PDU.

Before each iteration step, the end of PDU condition is tested.
If the end of PDU is reached, then the processing of the iteration stops immediately.
Otherwise, the referenced `DATA-OBJECT-PROP` is used to calculate a physical value of the parameter at the current position in the PDU.

Before the first iteration, this is the byte position of the `DYNAMIC-ENDMARKER-FIELD`.

If the resulting physical value matches the `TERMINATION-VALUE` (inside `DATA-OBJECT-PROP-REF`), the field ends without any additional item.
Therefore, the value inside the `TERMINATION-VALUE` shall be given in the physical type of this referenced `DATA-OBJECT-PROP`.

> [!NOTE]
> If an additional item is desired, a parameter referencing the same `BASIC-STRUCTURE` or `ENV-DATA-DESC` might follow the parameter referencing this `DYNAMIC-ENDMARKER-FIELD`.

The reference to the `BASIC-STRUCTURE` or `ENV-DATA-DESC` defines the complex DOP to be repeatedly applied.

For the first item, the byte position is given by the byte position of the `DYNAMIC-ENDMARKER-FIELD`.

Each further item starts at the byte edge following the item before (similar to `PARAM`s without explicitly specified `BYTE-POSITION`).

The bytes defined by the `ENDMARKER` are not considered to be consumed.
A parameter without `BYTE-POSITION` defined after the `ENDMARKER-FIELD` starts directly after the last structure of the field.
If the interpretation of the `ENDMARKER` bytes is not desired, they can be skipped with a `RESERVED` parameter.


## End of PDU field: MCD-2D V2.2 - 7.3.6.10.6

`END-OF-PDU-FIELD`s are similar to `DYNAMIC-ENDMARKER-FIELD`s, with the difference 
that the item is always repeated until the end of the PDU.

In the case of analyzing a response, the values of `MAX-NUMBER-OF-ITEMS` and
`MIN-NUMBER-OF-ITEMS` are ignored.

Before each iteration step, the end of PDU condition is tested.
If the end of PDU is reached, then the processing of the iteration stops immediately.

The reference to the `BASIC-STRUCTURE` or `ENV-DATA-DESC` defines the `COMPLEX-DOP`
to be repeatedly applied.

For the first item, the byte position is given by the `BYTE-POSITION`
of the `END-OF-PDU-FIELD`.

Each further item starts at the byte edge following the item before
(similar to `PARAM`s without explicitly specified `BYTE-POSITION`).


## Multiplexer: MCD-2D V2.2 - 7.3.6.10.7

`MUX`es are used to interpret data stream depending on the value of a switch-key
(similar to switch-case statements in programming languages like C or Java).

The determination of the actual switch-key is described inside `SWITCH-KEY`.
Its `BYTE-POSITION` is relative to the that of the `MUX`.
The optional `BIT-POSITION` shall be between 0 and 7.
The `DATA-OBJECT-PROP` referenced to is used to calculate the switch-key,
which is contained in its physical value.
The `DIAG-CODED-TYPE` of that `DATA-OBJECT-PROP` shall be of type `STANDARD-LENGTH-TYPE`.

Any number of `CASE`s can be specified.

If a `MUX` object has no `CASES` sub-object then it shall have a `DEFAULT-CASE` sub-object.

Each of them defines a `LOWER-LIMIT` and an `UPPER-LIMIT`.
The values shall match the physical type of the switch-key. [^1]
The ranges defined by the `CASE`s shall not overlap.

The actual value of the switch-key is compared with the values inside `LOWER-LIMIT`
and `UPPER-LIMIT` in the same way as for `SCALE-CONSTR` and `COMPU-SCALE` (see 7.3.6.2).
The comparison rules are described in section 7.3.6.5.

If the physical type is **A_UNICODE2STRING**, only identity is allowed, i.e. `LOWER-LIMIT`
and `UPPER-LIMIT` shall be equal. [^1]

If a matching `CASE` is found, the referenced `STRUCTURE` is analyzed at the
`BYTE-POSITION` (child element of `MUX`), relatively to the byte position of the `MUX`.
If a matching `CASE` cannot be found and the optional `DEFAULT-CASE` is specified,
then the `STRUCTURE` referenced by this `DEFAULT-CASE` is analyzed in the same way.
Otherwise, the D-server shall report an error.

The reference to the `STRUCTURE` is optional inside `CASE` and `DEFAULT-CASE`.
If it is not specified, the D-server will not signal an error condition if this
case has to be used.
By this way it is possible to specify a `CASE` or `DEFAULT-CASE` with the only purpose to
prevent an error message of the D-server, i.e. because the actual value of the
switch-key is valid, but it is not connected with further data.

[^1]: **Data type of `MUX`'s `SWITCH-KEY`**

    It seems like the `LOWER-LIMIT` and `UPPER-LIMIT` of `MUX`es are always specified as Unicode strings
    in MCD Projects, even though the `SWITCH-KEY` is an integer.
    
    They are allowed to be non-equal (specify a range), contrary to what is described above.
